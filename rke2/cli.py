#!/usr/bin/env python3

import json
import os
import re
import tempfile
from itertools import chain
from pathlib import Path
from subprocess import CalledProcessError, run
from typing import Annotated

import pydantic
import requests
import typer
import yaml
from deepmerge import always_merger as merger
from rich.console import Console
from ruamel.yaml import YAML, CommentedMap, CommentedSeq

DEFAULT_DIRECTORIES = [Path("argocd/applications"), Path("playbooks/templates")]
DEFAULT_GALAXY_PATH = Path("galaxy.yml")
DEFAULT_ARGOCD_PATH = Path("roles/components/defaults/main/argocd.yml")
VERSION_REGEX = r"v?[0-9]+\.[0-9]+\.[0-9]+$"
# Variables named *_image in tracked role defaults and playbook vars
DEFAULT_IMAGE_VARIABLE_GLOBS = ["roles/*/defaults/**/*.yml", "playbooks/vars/*.yml"]
# image: keys at any depth in tracked manifests (e.g. Helm values in ArgoCD apps)
DEFAULT_IMAGE_MANIFEST_GLOBS = ["argocd/applications/*.yml", "playbooks/templates/**/*.yml"]
# Tags that are a dotted version, optionally v-prefixed, optionally with a
# variant suffix (-debian). A candidate must match the pinned tag's suffix
# exactly, so a plain pin never moves to -rc1/-alpine and a -debian pin stays
# on -debian; anything else (latest, _large_disk, ...) is never a candidate
IMAGE_TAG_REGEX = r"^(?P<prefix>v?)(?P<version>[0-9]+(?:\.[0-9]+)*)(?P<suffix>-[a-z][a-z0-9.-]*)?$"
YAML_LINE_LENGTH = 160  # keep dumped yaml within the .yamllint line-length budget

type Version = str
type Versions = list[Version]
type HelmChartVersions = dict[str, Versions]
type LogLevel = int


class Application(pydantic.BaseModel):
    """Pydantic model representing an ArgoCD Application manifest."""

    class Spec(pydantic.BaseModel):
        class Source(pydantic.BaseModel):
            repoURL: str | None = None
            chart: str
            targetRevision: str = "HEAD"

        source: Source

    path: Path
    apiVersion: str
    kind: str
    spec: Spec


class HelmChart(pydantic.BaseModel):
    """Pydantic model representing a Helm chart entry in index.yaml."""

    name: str
    version: str


class HelmIndex(pydantic.BaseModel):
    """Pydantic model representing a Helm repository index.yaml."""

    entries: dict[str, list[HelmChart]]


class Collection(pydantic.BaseModel):
    """Pydantic model representing an Ansible Galaxy collection."""

    name: str
    version: str


class ChartPin(pydantic.BaseModel):
    """Pydantic model representing a chart pinned by a {name, repo, release} variable."""

    path: Path
    variable: str
    name: str
    repo: str
    release: str


class Image(pydantic.BaseModel):
    """Pydantic model representing a pinned container image reference in a file."""

    path: Path
    reference: str
    repository: str
    tag: str


def format_yaml(data: object) -> object:
    """
    Format YAML data
    """
    if isinstance(data, list):
        seq = CommentedSeq(data)
        for idx in range(len(seq)):
            seq.yaml_set_comment_before_after_key(idx, after="\n")  # pyright: ignore[reportUnknownMemberType]
        return seq
    if isinstance(data, dict):
        cm = CommentedMap(data)
        items_all = cm.items()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        items_first = list(items_all)[0][0]  # pyright: ignore[reportUnknownArgumentType, reportUnknownVariableType]
        for key, value in items_all:  # pyright: ignore[reportUnknownVariableType]
            cm[key] = format_yaml(value)  # pyright: ignore[reportUnknownArgumentType]
            if key != items_first:
                cm.yaml_set_comment_before_after_key(key, before="\n")  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
        return cm
    return data


def create_http_session() -> requests.Session:
    """Create and configure HTTP session for Helm repository requests."""
    session = requests.Session()
    session.headers.update({"User-Agent": "ArgoCD-Chart-Updater/1.0"})
    return session


def find_yaml_files(directory: Path) -> list[Path]:
    """Find all YAML files under directory, subdirectories included (playbooks/templates/vector/)."""
    return list(directory.rglob("*.yaml")) + list(directory.rglob("*.yml"))


def flatten[T](elements: list[list[T]]) -> list[T]:
    """Flatten a list of lists."""
    return list(chain.from_iterable(elements))


def argocd_application(file: Path) -> Application | None:
    """Check if a file is an ArgoCD Application manifest by looking for 'apiVersion' and 'kind'."""
    try:
        with file.open("r") as f:
            app_data = merger.merge(yaml.safe_load(f), {"path": file})  # pyright: ignore[reportAny]
            app: Application = Application(**app_data)  # pyright: ignore[reportAny]
            if app.apiVersion.startswith("argoproj.io/") and app.kind == "Application":
                return app
    except (yaml.YAMLError, FileNotFoundError, pydantic.ValidationError):
        pass
    except AttributeError as e:
        typer.echo(f"Error parsing file {file}: {e}")
    return None


def argocd_application_chart(file: Path) -> Application | None:
    """Check if a file is an ArgoCD Application manifest with a Helm chart."""
    try:
        app = argocd_application(file)
        if app and app.spec and app.spec.source and app.spec.source.repoURL and app.spec.source.chart:
            return app
    except AttributeError as e:
        typer.echo(f"Error parsing file {file}: {e}")
    return None


def create_file(path: Path, content: str | None = None) -> None:
    """Create a file with the given content."""

    try:
        with path.open("w") as f:
            if content is not None:
                _ = f.write(content)
            f.flush()
    except FileNotFoundError as e:
        typer.echo(f"Error creating file {path}: {e}")
    except IOError as e:
        typer.echo(f"Error writing to file {path}: {e}")


def argocd_application_helm_index(app: Application) -> HelmChart | None:
    """Retrieve and parse Helm repository using Helm commands"""
    return helm_chart_latest(app.spec.source.chart, app.spec.source.repoURL)


def helm_chart_latest(chart_name: str, chart_repo: str | None) -> HelmChart | None:
    """Find the latest published version of a chart in an http or oci repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_repository = Path(temp_dir) / "repository.yaml"
        config_registry = Path(temp_dir) / "registry.yaml"
        config_cache = Path(temp_dir) / "cache"
        create_file(config_repository)
        create_file(config_registry)
        _ = os.makedirs(config_cache, exist_ok=True)
        try:
            if not chart_repo:
                typer.echo(f"Skipping chart {chart_name} due to missing repoURL.")
                return None
            if chart_repo.startswith("http"):
                helm_config = f"--registry-config {config_registry} --repository-config {config_repository} --repository-cache {config_cache}"
                cmd_add = f"helm repo add {chart_name} {chart_repo} {helm_config}"
                _ = run(cmd_add.split(), check=True, capture_output=True, text=True)
                cmd_update = f"helm repo update {chart_name} {helm_config}"
                _ = run(cmd_update.split(), check=True, capture_output=True, text=True)
                cmd_search = f"helm search repo {chart_name}/{chart_name} --output json {helm_config}"
                result = run(cmd_search.split(), check=True, capture_output=True, text=True)
                chart_data = yaml.safe_load(result.stdout.strip())  # pyright: ignore[reportAny]
                chart = HelmChart(**chart_data[0])  # pyright: ignore[reportAny]
                return chart
            else:
                cmd_show = f"helm show chart oci://{chart_repo}/{chart_name}"
                result = run(cmd_show.split(), check=True, capture_output=True, text=True)
                chart_data = yaml.safe_load(result.stdout.strip())  # pyright: ignore[reportAny]
                chart = HelmChart(**chart_data)  # pyright: ignore[reportAny]
                return chart
        except (CalledProcessError, yaml.YAMLError, FileNotFoundError):
            typer.echo(f"Error fetching Helm chart index for {chart_repo}")
            return None
        except (AttributeError, requests.HTTPError) as e:
            typer.echo(f"Error parsing Helm index data: {e}")
            return None


def collection_version(path: Path) -> str:
    """Get the version of the collection from galaxy.yml."""
    try:
        if path.exists() and path.is_file():
            with path.open("r") as f:
                collection = Collection(**yaml.safe_load(f))  # pyright: ignore[reportAny]
                return str(collection.version)
    except FileNotFoundError as e:
        typer.echo(f"Error reading {path}: {e}")
    except yaml.YAMLError as e:
        typer.echo(f"Error parsing {path}: {e}")
    except AttributeError as e:
        typer.echo(f"Error parsing Collection metadata: {e}")
    return ""


def argocd_version(path: Path) -> str:
    """Get the version of the collection from galaxy.yml."""
    try:
        if path.exists() and path.is_file():
            with path.open("r") as f:
                data = yaml.safe_load(f)  # pyright: ignore[reportAny]
                return str(data.get("rke2_argocd_apps_pokerops_revision", ""))  # pyright: ignore[reportAny]
    except FileNotFoundError as e:
        typer.echo(f"Error reading {path}: {e}")
    except yaml.YAMLError as e:
        typer.echo(f"Error parsing {path}: {e}")
    return ""


def yaml_attribute_update(file: Path, attribute: dict) -> None:  # pyright: ignore[reportMissingTypeArgument, reportUnknownParameterType]
    """Update attribute in yaml file."""
    ruamel = YAML(typ="rt")
    ruamel.preserve_quotes = True  # type: ignore
    ruamel.explicit_start = True  # type: ignore
    ruamel.width = YAML_LINE_LENGTH  # type: ignore
    ruamel.indent(mapping=2, sequence=4, offset=2)  # pyright: ignore[reportUnknownMemberType]
    try:
        with file.open("r") as f:
            app_current = ruamel.load(f)  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
            app_updated = merger.merge(  # pyright: ignore[reportUnknownVariableType]
                app_current.copy(),  # pyright: ignore[reportUnknownArgumentType, reportUnknownMemberType]
                attribute,  # pyright: ignore[reportUnknownArgumentType]
            )
        with file.open("w") as f:
            ruamel.dump(app_updated, f)  # pyright: ignore[reportUnknownMemberType]
            f.flush()
    except AttributeError as e:
        typer.echo(f"Error opening file {file}: {e}")


def tracked_files(globs: list[str]) -> list[Path]:
    """List git-tracked files matching globs, so vendored/ignored roles are never touched."""
    try:
        result = run(["git", "ls-files", "-z", "--", *globs], check=True, capture_output=True, text=True)
    except (CalledProcessError, FileNotFoundError) as e:
        typer.echo(f"Error listing tracked files: {e}")
        return []
    return [Path(name) for name in result.stdout.split("\0") if name]


def image_reference(path: Path, reference: str) -> Image | None:
    """Parse a pinned repository:tag reference; templated and digest-pinned references are skipped."""
    if "{{" in reference or "@" in reference:
        typer.echo(f"Skipping image {reference} in {path}: templated or digest-pinned.")
        return None
    repository, sep, tag = reference.rpartition(":")
    if not sep or "/" in tag:
        typer.echo(f"Skipping image {reference} in {path}: no tag.")
        return None
    return Image(path=path, reference=reference, repository=repository, tag=tag)


def load_yaml_documents(path: Path) -> list[object]:
    """Load every YAML document in a file; files that are not plain YAML (e.g. jinja templates) yield none."""
    try:
        with path.open("r") as f:
            return [doc for doc in yaml.safe_load_all(f) if doc is not None]  # pyright: ignore[reportAny]
    except (yaml.YAMLError, FileNotFoundError):
        return []


def manifest_image_values(data: object) -> list[str]:
    """Collect string values of image: keys at any depth."""
    if isinstance(data, dict):
        return flatten(
            [
                [value] if key == "image" and isinstance(value, str) else manifest_image_values(value)  # pyright: ignore[reportUnknownArgumentType]
                for key, value in data.items()  # pyright: ignore[reportUnknownVariableType]
            ]
        )
    if isinstance(data, list):
        return flatten([manifest_image_values(item) for item in data])  # pyright: ignore[reportUnknownVariableType]
    return []


def variable_image_values(data: object) -> list[str]:
    """Collect string values of top-level variables named *_image."""
    if not isinstance(data, dict):
        return []
    return [value for key, value in data.items() if str(key).endswith("_image") and isinstance(value, str)]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]


def find_images(variable_globs: list[str], manifest_globs: list[str]) -> list[Image]:
    """Find pinned images in role/playbook variables and manifest image: keys."""
    sources = [(path, variable_image_values) for path in tracked_files(variable_globs)] + [
        (path, manifest_image_values) for path in tracked_files(manifest_globs)
    ]
    return [
        image
        for path, extract in sources
        for doc in load_yaml_documents(path)
        for value in extract(doc)
        if (image := image_reference(path, value))
    ]


def registry_repository(repository: str) -> str:
    """Fully qualify a repository so skopeo does not depend on local short-name config."""
    host = repository.split("/", 1)[0]
    if "/" in repository and ("." in host or ":" in host or host == "localhost"):
        return repository
    return f"docker.io/{repository if '/' in repository else f'library/{repository}'}"


def image_tags(repository: str) -> list[str] | None:
    """List the tags published for a repository."""
    try:
        cmd = ["skopeo", "list-tags", f"docker://{registry_repository(repository)}"]
        result = run(cmd, check=True, capture_output=True, text=True)
        return list(json.loads(result.stdout)["Tags"])  # pyright: ignore[reportAny]
    except FileNotFoundError:
        typer.echo("skopeo command not found. Please ensure skopeo is installed.")
    except (CalledProcessError, json.JSONDecodeError, KeyError) as e:
        typer.echo(f"Error listing tags for {repository}: {e}")
    return None


def latest_tag(current: str, tags: list[str]) -> str | None:
    """Pick the highest tag shaped like the current one (same v-prefix, number of components and variant suffix)."""
    if not (match := re.match(IMAGE_TAG_REGEX, current)):
        return None
    shape = (match["prefix"], match["version"].count("."), match["suffix"])
    candidates = [
        m for tag in tags if (m := re.match(IMAGE_TAG_REGEX, tag)) and (m["prefix"], m["version"].count("."), m["suffix"]) == shape
    ]
    if not candidates:
        return None
    newest = max(candidates, key=lambda m: tuple(int(part) for part in m["version"].split(".")))
    return newest.string


def image_reference_update(path: Path, current: str, updated: str) -> None:
    """Replace a whole image reference in place, preserving the file's formatting and comments."""
    # Boundaries keep repo:v1.1 from matching inside repo:v1.14.1
    pattern = rf"(?<![\w./-]){re.escape(current)}(?![\w.-])"
    try:
        content = path.read_text()
        _ = path.write_text(re.sub(pattern, updated, content))
    except IOError as e:
        typer.echo(f"Error updating file {path}: {e}")


def variable_chart_pins(path: Path, data: object) -> list[ChartPin]:
    """Collect top-level variables shaped like a chart pin: a mapping with string name, repo and release."""
    if not isinstance(data, dict):
        return []
    return [
        ChartPin(path=path, variable=str(key), name=value["name"], repo=value["repo"], release=value["release"])  # pyright: ignore[reportUnknownArgumentType]
        for key, value in data.items()  # pyright: ignore[reportUnknownVariableType]
        if isinstance(value, dict)
        and all(isinstance(value.get(field), str) for field in ("name", "repo", "release"))  # pyright: ignore[reportUnknownMemberType]
        and not any("{{" in value[field] for field in ("name", "repo", "release"))
    ]


def find_chart_pins(variable_globs: list[str]) -> list[ChartPin]:
    """Find chart pins in role/playbook variables."""
    return [
        pin
        for path in tracked_files(variable_globs)
        for doc in load_yaml_documents(path)
        for pin in variable_chart_pins(path, doc)
    ]


def chart_pin_update(pin: ChartPin, release: str) -> None:
    """Rewrite the release line inside one pin variable's block, preserving formatting, comments and quoting."""
    try:
        lines = pin.path.read_text().splitlines(keepends=True)
    except IOError as e:
        typer.echo(f"Error reading file {pin.path}: {e}")
        return
    start = next((n for n, line in enumerate(lines) if re.match(rf"^{re.escape(pin.variable)}:\s*$", line)), None)
    if start is None:
        typer.echo(f"Skipping chart {pin.name}: variable {pin.variable} not found as a block in {pin.path}.")
        return
    for n in range(start + 1, len(lines)):
        if lines[n].strip() and not lines[n][0].isspace():
            break  # next top-level key: this block has no release line of its own
        if match := re.match(r"^(\s+release:\s*)([\"']?)([^\"'\s#]+)([\"']?)(.*)$", lines[n], re.DOTALL):
            lines[n] = f"{match[1]}{match[2]}{release}{match[4]}{match[5]}"
            _ = pin.path.write_text("".join(lines))
            return
    typer.echo(f"Skipping chart {pin.name}: no release line under {pin.variable} in {pin.path}.")


def update_chart_pins(dry_run: bool) -> None:
    """Update {name, repo, release} chart pin variables to the latest published chart version."""
    for pin in find_chart_pins(DEFAULT_IMAGE_VARIABLE_GLOBS):
        index = helm_chart_latest(pin.name, pin.repo)
        if index is None:
            typer.echo(f"Skipping chart {pin.name} update due to index fetch error.")
            continue
        if index.version == pin.release:
            typer.echo(f"Chart {pin.name} is already up to date at version {pin.release}.")
            continue
        typer.echo(f"Updating chart {pin.name} ({pin.variable} in {pin.path}) from version {pin.release} to {index.version}.")
        if not dry_run:
            chart_pin_update(pin, index.version)


def update_charts(directories: list[Path], dry_run: bool) -> None:
    """Update ArgoCD Application Helm chart versions to latest."""
    yaml_files = flatten([find_yaml_files(directory) for directory in directories])
    if not yaml_files:
        typer.echo(f"No YAML files found in {', '.join([str(d) for d in directories])}")
        return

    helm_charts = [chart for file in yaml_files if (chart := argocd_application_chart(file))]
    indices = [argocd_application_helm_index(chart) for chart in helm_charts]
    for index, chart in zip(indices, helm_charts):
        _name = chart.spec.source.chart
        if index is None:
            typer.echo(f"Skipping chart {_name} update due to index fetch error.")
            continue
        _vold = chart.spec.source.targetRevision
        _vnew = index.version
        if _vold == _vnew:
            typer.echo(f"Chart {_name} is already up to date at version {_vold}.")
            continue
        typer.echo(f"Updating chart {_name} from version {_vold} to {_vnew}.")
        if not dry_run:
            yaml_attribute_update(chart.path, {"spec": {"source": {"targetRevision": _vnew}}})


def update_images(dry_run: bool) -> None:
    """Update pinned container image tags to the latest published version."""
    images = find_images(DEFAULT_IMAGE_VARIABLE_GLOBS, DEFAULT_IMAGE_MANIFEST_GLOBS)
    tags = {repository: image_tags(repository) for repository in {image.repository for image in images}}
    for image in images:
        _tags = tags[image.repository]
        if _tags is None:
            typer.echo(f"Skipping image {image.repository} update due to tag fetch error.")
            continue
        _vnew = latest_tag(image.tag, _tags)
        if _vnew is None:
            typer.echo(f"Skipping image {image.reference} in {image.path}: tag is not a plain version.")
            continue
        if _vnew == image.tag:
            typer.echo(f"Image {image.repository} is already up to date at version {image.tag}.")
            continue
        typer.echo(f"Updating image {image.repository} in {image.path} from version {image.tag} to {_vnew}.")
        if not dry_run:
            image_reference_update(image.path, image.reference, f"{image.repository}:{_vnew}")


app = typer.Typer(help="Manage Helm chart and container image versions")


@app.command()
def update(
    directories: list[Path] = DEFAULT_DIRECTORIES,
    dry_run: Annotated[bool, typer.Option(help="Skip manifest updates")] = False,
) -> None:
    """Update ArgoCD Application Helm chart versions, chart pin variables and pinned container images to latest."""
    update_charts(directories, dry_run)
    update_chart_pins(dry_run)
    update_images(dry_run)


@app.command()
def build(
    galaxy_path: Path = DEFAULT_GALAXY_PATH,
    argocd_path: Path = DEFAULT_ARGOCD_PATH,
    check: Annotated[bool, typer.Option(help="Fail on version drift instead of updating")] = False,
) -> None:
    """Build the application."""
    _collection_version = collection_version(galaxy_path)
    assert _collection_version, f"Collection version not found in {galaxy_path}"
    _argocd_version = argocd_version(argocd_path)
    assert _argocd_version, f"ArgoCD version not found in {argocd_path}"
    if _argocd_version != _collection_version:
        if check:
            typer.echo(
                f"ArgoCD version {_argocd_version} does not match collection version {_collection_version}, please run 'just build-fix' and commit changes",
                err=True,
            )
            exit(1)
        typer.echo(f"Updating ArgoCD version from {_argocd_version} to {_collection_version}.")
        yaml_attribute_update(argocd_path, {"rke2_argocd_apps_pokerops_revision": _collection_version})
    else:
        typer.echo(f"ArgoCD version {_argocd_version} is already up to date.")

    try:
        typer.echo("Building Ansible Galaxy collection...")
        result = run(["ansible-galaxy", "collection", "build", "--force"], check=True, capture_output=True, text=True)
        typer.echo("Collection built successfully!")
        if result.stdout:
            typer.echo(result.stdout.strip())
    except CalledProcessError as e:
        typer.echo(f"Error building collection: {e}", err=True)
        exit(1)
    except FileNotFoundError:
        typer.echo("ansible-galaxy command not found. Please ensure Ansible is installed.", err=True)
        exit(1)


def main() -> None:
    """Main function to run the update command."""
    app()


if __name__ == "__main__":
    main()

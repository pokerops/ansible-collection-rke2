#!/usr/bin/env python3

import os
import tempfile
from itertools import chain
from pathlib import Path
from re import match
from subprocess import CalledProcessError, run
from typing import Annotated

import pydantic
import requests
import typer
import yaml
from deepmerge import always_merger as merger
from ruamel.yaml import YAML, CommentedMap, CommentedSeq

DEFAULT_DIRECTORIES = [Path("argocd/applications"), Path("playbooks/templates")]
DEFAULT_GALAXY_PATH = Path("galaxy.yml")
DEFAULT_ARGOCD_PATH = Path("roles/components/defaults/main/argocd.yml")
VERSION_REGEX = r"v?[0-9]+\.[0-9]+\.[0-9]+$"

type Version = str
type Versions = list[Version]
type HelmChartVersions = dict[str, Versions]
type LogLevel = int


class Application(pydantic.BaseModel):
    """Pydantic model representing an ArgoCD Application manifest."""

    class Spec(pydantic.BaseModel):
        class Source(pydantic.BaseModel):
            repoURL: str
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
    """Find all YAML files in directory."""
    return list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))


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
    except (yaml.YAMLError, FileNotFoundError):
        pass
    except AttributeError as e:
        typer.echo(f"Error parsing file {file}: {e}")
    return None


def argocd_application_chart(file: Path) -> Application | None:
    """Check if a file is an ArgoCD Application manifest with a Helm chart."""
    try:
        app = argocd_application(file)
        if app and app.spec.source.repoURL.startswith("http") and app.spec.source.chart:
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


def argocd_application_helm_index(session: requests.Session, app: Application) -> HelmChart | None:
    """Retrieve and parse Helm repository using Helm commands"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_repository = Path(temp_dir) / "repository.yaml"
        config_registry = Path(temp_dir) / "registry.yaml"
        config_cache = Path(temp_dir) / "cache"
        create_file(config_repository)
        create_file(config_registry)
        _ = os.makedirs(config_cache, exist_ok=True)
        try:
            chart_name = app.spec.source.chart
            chart_repo = app.spec.source.repoURL
            helm_config = ["--registry-config", str(config_registry), "--repository-config", str(config_repository), "--repository-cache", str(config_cache)]
            _ = run(["helm", "repo", "add", chart_name, chart_repo] + helm_config, check=True, capture_output=True, text=True)
            _ = run(["helm", "repo", "update", chart_name] + helm_config, check=True, capture_output=True, text=True)
            result = run(["helm", "search", "repo", f"{chart_name}/{chart_name}", "--output", "json"] + helm_config, check=True, capture_output=True, text=True)
            chart_data = yaml.safe_load(result.stdout.strip())  # pyright: ignore[reportAny]
            chart = HelmChart(**chart_data[0])  # pyright: ignore[reportAny]
            return chart
        except (CalledProcessError, yaml.YAMLError, FileNotFoundError):
            typer.echo(f"Error fetching Helm chart index for {app.spec.source.repoURL}")
            return None
        except AttributeError as e:
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


app = typer.Typer(help="Manage Helm chart versions")


@app.command()
def update(
    directories: list[Path] = DEFAULT_DIRECTORIES,
    dry_run: Annotated[bool, typer.Option(help="Skip manifest updates")] = False,
) -> None:
    """Update ArgoCD Application Helm chart versions to latest."""

    yaml_files = flatten([find_yaml_files(directory) for directory in directories])
    if not yaml_files:
        typer.echo(f"No YAML files found in {', '.join([str(d) for d in directories])}")
        return

    charts = [chart for file in yaml_files if (chart := argocd_application_chart(file))]
    session = create_http_session()
    indices = [argocd_application_helm_index(session, chart) for chart in charts]
    for index, chart in zip(indices, charts):
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


@app.command()
def build(galaxy_path: Path = DEFAULT_GALAXY_PATH, argocd_path: Path = DEFAULT_ARGOCD_PATH) -> None:
    """Build the application."""
    _collection_version = collection_version(galaxy_path)
    assert _collection_version, f"Collection version not found in {galaxy_path}"
    _argocd_version = argocd_version(argocd_path)
    assert _argocd_version, f"ArgoCD version not found in {galaxy_path}"
    if _argocd_version != _collection_version:
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

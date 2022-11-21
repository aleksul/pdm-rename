import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

from pdm.core import Core
from pdm.project import Project
from pdm.signals import post_build, pre_build


def parse_config(project: Project) -> Optional[Dict[str, str]]:
    pyproject = project.pyproject
    if (
        pyproject is None
        or "tool" not in pyproject
        or "pdm" not in pyproject["tool"]
        or "rename" not in pyproject["tool"]["pdm"]
    ):
        return None

    rename_config: Dict[str, str] = pyproject["tool"]["pdm"]["rename"]

    if (
        not isinstance(rename_config, Dict)
        or not all(isinstance(i, str) for i in rename_config.keys())
        or not all(isinstance(i, str) for i in rename_config.values())
    ):
        project.core.ui.echo("tool.pdm.rename must be a dictionary of strings.", err=True)
        return None

    return rename_config


def parse_rename(
    project: Project,
    rename_config: Dict[str, str],
    rename_back: bool = False,
) -> Dict[Path, Path]:
    result: Dict[Path, Path] = {}

    for initial_name, rename_to in rename_config.items():

        initial_path = project.root.joinpath(Path(initial_name))
        rename_to_path = project.root.joinpath(Path(rename_to))

        if not rename_back and not initial_path.exists():
            project.core.ui.echo(
                f"Directory '{initial_name}' doesn't exist, no renaming.", err=True
            )
            continue

        if rename_back and not rename_to_path.exists():
            project.core.ui.echo(f"Directory '{rename_to}' doesn't exist, no renaming.", err=True)
            continue

        if rename_back and initial_path.exists():
            project.core.ui.echo(
                f"Directory '{initial_name}' already exists, no renaming.", err=True
            )
            continue

        if not rename_back and rename_to_path.exists():
            project.core.ui.echo(f"Directory '{rename_to}' already exists, no renaming.", err=True)
            continue

        if not rename_back and not initial_path.is_dir():
            project.core.ui.echo(f"{initial_name}' is not a directory, no renaming.", err=True)
            continue

        if rename_back and not rename_to_path.is_dir():
            project.core.ui.echo(f"{rename_to}' is not a directory, no renaming.", err=True)
            continue

        result[initial_path] = rename_to_path

    return result


def get_subroot_project_folder(root: Path, path: Path) -> Path:
    return root.joinpath(path.relative_to(root).parts[0])


def on_pre_build(project: Project, *_args: Tuple, **_kwargs: Dict) -> None:
    rename_config = parse_config(project)

    if rename_config is None:
        return

    for initial_path, rename_to_path in parse_rename(project, rename_config).items():
        project.core.ui.echo(f"Renaming '{initial_path}' -> '{rename_to_path}'")
        # rename to a new folder
        rename_to_path.mkdir(parents=True)
        initial_path.rename(rename_to_path)
        # delete folder from the project root
        shutil.rmtree(get_subroot_project_folder(project.root, initial_path), ignore_errors=True)


def on_post_build(project: Project, *_args: Tuple, **_kwargs: Dict) -> None:
    rename_config = parse_config(project)

    if rename_config is None:
        return

    for initial_path, rename_to_path in parse_rename(
        project, rename_config, rename_back=True
    ).items():
        project.core.ui.echo(f"Renaming back '{rename_to_path}' -> '{initial_path}'")
        # rename back
        initial_path.mkdir(parents=True)
        rename_to_path.rename(initial_path)
        # delete folder from the project root
        shutil.rmtree(get_subroot_project_folder(project.root, rename_to_path), ignore_errors=True)


def rename_plugin(_: Core) -> None:
    pre_build.connect(on_pre_build)
    post_build.connect(on_post_build)

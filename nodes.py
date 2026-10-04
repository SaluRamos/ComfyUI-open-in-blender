import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import winreg

from comfy_api.latest import Types
from comfy_extras.nodes_save_3d import mesh_item_to_glb_bytes


def _blender_executable():
    configured = os.environ.get("BLENDER_EXE")
    if configured and Path(configured).is_file():
        return configured

    executable = shutil.which("blender.exe") or shutil.which("blender")
    if executable:
        return executable

    registry_paths = (
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    )
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for registry_path in registry_paths:
            try:
                root = winreg.OpenKey(hive, registry_path)
            except OSError:
                continue
            with root:
                for index in range(winreg.QueryInfoKey(root)[0]):
                    try:
                        with winreg.OpenKey(root, winreg.EnumKey(root, index)) as entry:
                            name = winreg.QueryValueEx(entry, "DisplayName")[0]
                            location = winreg.QueryValueEx(entry, "InstallLocation")[0]
                    except OSError:
                        continue
                    if name.startswith("Blender") and location:
                        candidate = Path(location) / "blender.exe"
                        if candidate.is_file():
                            return str(candidate)

    roots = (
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Blender Foundation",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Blender Foundation",
    )
    for root in roots:
        if root.is_dir():
            for candidate in sorted(root.glob("Blender */blender.exe"), reverse=True):
                if candidate.is_file():
                    return str(candidate)
    return None


def _import_script(paths, temporary_directory):
    payload = base64.b64encode(json.dumps({
        "paths": [str(path) for path in paths],
        "temporary_directory": str(temporary_directory),
    }).encode("utf-8")).decode("ascii")
    script = f'''\
import base64
import json
import shutil
import bpy

payload = json.loads(base64.b64decode("{payload}"))
try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for path in payload["paths"]:
        bpy.ops.import_scene.gltf(filepath=path)
finally:
    shutil.rmtree(payload["temporary_directory"], ignore_errors=True)
'''
    return base64.b64encode(script.encode("utf-8")).decode("ascii")


class OpenInBlender:
    CATEGORY = "3d/Blender"
    FUNCTION = "open_in_blender"
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    DESCRIPTION = "Open Blender and import the MESH geometry, UVs and materials."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"mesh": ("MESH",)}}

    def open_in_blender(self, mesh):
        blender = _blender_executable()
        if blender is None:
            raise RuntimeError(
                "Blender was not found. Add blender.exe to PATH or set the BLENDER_EXE environment variable."
            )

        directory = Path(__file__).resolve().parent / ".temp"
        directory.mkdir(exist_ok=True)
        temporary_directory = Path(tempfile.mkdtemp(prefix="open-in-blender-", dir=directory))
        try:
            paths = []
            for index in range(mesh.vertices.shape[0]):
                data = mesh_item_to_glb_bytes(mesh, index)
                if data is None:
                    raise ValueError(f"MESH batch item {index} has no geometry to import.")
                path = temporary_directory / f"mesh_{index}.glb"
                path.write_bytes(data)
                paths.append(path)

            expression = _import_script(paths, temporary_directory)
            subprocess.Popen(
                [blender, "--python-expr", f"exec(__import__('base64').b64decode('{expression}'))"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        except Exception:
            shutil.rmtree(temporary_directory, ignore_errors=True)
            raise
        return ()


NODE_CLASS_MAPPINGS = {"ComfyUIOpenInBlender": OpenInBlender}
NODE_DISPLAY_NAME_MAPPINGS = {"ComfyUIOpenInBlender": "Open in Blender"}

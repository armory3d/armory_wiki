"""
Takes screenshots from all of Armory's logic nodes.

WARNING:
    this script will reset your theme, so make sure it's saved!

USAGE:
    Set the OUTPUT_PATH variable to the "logic_nodes" directory of the
    Armory wiki images repository. Then, open this file in Blender's
    text editor in a new blender file and run it. Blender might freeze
    during the run, but the screenshots should be correct nonetheless.
    It is still advised to check them afterwards.

    For keeping the images repository size small, please only commit
    screenshots with visible changes. Even if nothing changed with the
    node, the screenshot file could have been changed.

    Runnning this script from the command line does not work (even if
    run with a window and UI) because command line scripts are executed
    before any OpenGL call is done (1).

    (1) https://stackoverflow.com/a/44971998/9985959
"""
import ensurepip
import os
import subprocess
import sys
from typing import List, Optional

import bpy

try:
    from PIL import Image
except ImportError:
    # Try to install Pillow into Blender's Python installation
    ensurepip.bootstrap()
    os.environ.pop("PIP_REQ_TRACKER", None)
    subprocess.check_output([sys.executable, '-m', 'pip', 'install', 'Pillow'])

    from PIL import Image

from arm.logicnode import arm_nodes

OUTPUT_PATH = "SET_THIS_AS_DESCRIBED_IN_THE_MODULE_DOCSTRING"
GRID_SIZE = 20
MARGIN = 20

WARNINGS: List[str] = []


def take_screenshot(file_path: str, editor: bpy.types.SpaceNodeEditor, nodetype: str):
    print("Creating screenshot of", nodetype)

    nodes = editor.node_tree.nodes
    node = nodes.new(nodetype)

    # Force node drawing so that node.dimensions is not (0, 0) because
    # Blender's UI is a immediate mode UI.
    bpy.ops.wm.redraw_timer(type="DRAW_WIN", iterations=1)
    bpy.context.area.tag_redraw()

    node.select = False

    # Show the entire node on the screen.
    node.location[1] += node.dimensions[1] + (node.dimensions[1] % GRID_SIZE)

    # Discard dynamic label
    node.label = node.bl_label

    # Take a screenshot of the active area
    bpy.ops.screen.screenshot("EXEC_DEFAULT", filepath=file_path, full=False)

    area = bpy.context.area
    # -1 = WINDOW region
    view2d = area.regions[-1].view2d
    # Convert node coordinates to "region/pixel space"
    left, top = view2d.view_to_region(node.location[0], node.location[1])
    right, bottom = view2d.view_to_region(node.location[0] + node.dimensions[0], node.location[1] - node.dimensions[1])

    bottom = area.height - bottom
    top = area.height - top

    left -= MARGIN
    right += MARGIN
    top -= MARGIN
    bottom += MARGIN

    # Check if the node is too big for a screenshot and warn later
    if bottom - top > bpy.context.area.height:
        WARNINGS.append(nodetype)
        nodes.remove(node)
        return

    nodes.remove(node)

    # Crop images
    img = Image.open(file_path)
    cropped: Image = img.crop((left, top, right, bottom))
    # Scale a bit down
    maxsize = (400, 1000)
    cropped.thumbnail(maxsize, Image.ANTIALIAS)
    # 95 = best quality as per Pillow documentation
    cropped.save(os.path.splitext(file_path)[0] + ".jpg", "JPEG", quality=95)

    # Delete original .png screenshot
    os.remove(file_path)


def run():
    # No UI when running windowless
    if bpy.app.background:
        print("Please do not run this script in background mode!")
        return

    print("Start creating screenshots. This might take a while...")

    bpy.ops.preferences.reset_default_theme()

    area = bpy.context.area
    area.type = "NODE_EDITOR"

    editor: Optional[bpy.types.SpaceNodeEditor] = None
    for space in area.spaces:
        if space.type == "NODE_EDITOR":
            space.tree_type = "ArmLogicTreeType"
            editor = space
            editor.node_tree = bpy.data.node_groups.new("ScreenshotNodes", "ArmLogicTreeType")

    bpy.ops.screen.screen_full_area(use_hide_panels=True)
    bpy.ops.view2d.reset("INVOKE_REGION_WIN")

    if bpy.context.area.x != 0 or bpy.context.area.y != 0:
        print("WARNING: Area coordinates are not (0, 0), screenshot cropping might be wrong!")

    # Set the zoom factor so that the screenshots have the same sizes
    # independent of the machine this script is executed on.
    # zoomfac[x/y] parameters have no effect here, so we need to execute
    # the operators a few times
    for i in range(50):
        bpy.ops.view2d.zoom_in("INVOKE_REGION_WIN", zoomfacx=1.0, zoomfacy=1.0)
    for i in range(4):
        bpy.ops.view2d.zoom_out("INVOKE_REGION_WIN", zoomfacx=1.0, zoomfacy=1.0)

    # Make tall nodes fit on the screen
    for i in range(4):
        bpy.ops.view2d.scroll_up("EXEC_REGION_WIN", deltax=0, deltay=0)

    for category in arm_nodes.get_all_categories():
        category_path = os.path.join(OUTPUT_PATH, category.name.lower())
        if not os.path.exists(category_path):
            os.makedirs(category_path)

        os.chdir(category_path)

        for nodeitem in category.get_all_nodes():
            node_path = os.path.join(category_path, nodeitem.nodetype + ".png")
            take_screenshot(node_path, editor, nodeitem.nodetype)

    bpy.data.node_groups.remove(editor.node_tree)

    if len(WARNINGS) > 0:
        print("The following nodes were too big for a screenshot:")

        for node in WARNINGS:
            print("\t" + node)


if __name__ == "__main__":
    run()

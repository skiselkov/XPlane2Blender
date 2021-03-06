# File: xplane_updater.py
# Automagically updates blend data created with older XPlane2Blender Versions

import bpy
from .xplane_config import *
from .xplane_constants import *
from bpy.app.handlers import persistent

def __upgradeLocRot(object):
    for d in object.xplane.datarefs:
        pre_34_anim_types = [
            ANIM_TYPE_TRANSFORM,
            ANIM_TYPE_TRANSLATE,
            ANIM_TYPE_ROTATE,
            ANIM_TYPE_SHOW,
            ANIM_TYPE_HIDE
            ]
            
        post_34_anim_types = [
            ANIM_TYPE_TRANSFORM,
            ANIM_TYPE_SHOW,
            ANIM_TYPE_HIDE
            ]
        
        old_anim_type = d.get('anim_type')
        if old_anim_type is None:
           old_anim_type = 0 #something about Blender properties requires this
        
        if old_anim_type < pre_34_anim_types.index(ANIM_TYPE_SHOW):
            new_anim_type = 0 #_TRANSFORM, _TRANSLATE, and _ROTATE are all now merged to _TRANSFORM (0)
        else:
            new_anim_type = old_anim_type - 2 #We removed 2 constants, hence, subtract two to map to the new list
        d.anim_type = post_34_anim_types[new_anim_type]
        
def __upgradeManip(object):
    #Since the order of the enum matters, the only way to really make this forwards compatabile is literally saving the old list.
    pre_34_manips = [
        MANIP_DRAG_XY,
        MANIP_DRAG_AXIS,
        MANIP_COMMAND,
        MANIP_COMMAND_AXIS,
        MANIP_PUSH,
        MANIP_RADIO,
        MANIP_DELTA,
        MANIP_WRAP,
        MANIP_TOGGLE,
        MANIP_NOOP,
        MANIP_DRAG_AXIS_PIX,
        MANIP_COMMAND_KNOB,
        MANIP_COMMAND_SWITCH_UP_DOWN,
        MANIP_COMMAND_SWITCH_LEFT_RIGHT,
        MANIP_AXIS_SWITCH_UP_DOWN,
        MANIP_AXIS_SWITCH_LEFT_RIGHT
        ]

    #Since enum type_1050 contains all of type, this is okay
    old_type = object.xplane.manip.get('type')
    if old_type is None:
        #Oddly enough, .get('type') for drag_xy is not an index of 0, but None!
        #To have no manipulator, Manipulator must be unchecked
        old_type = 0 
 
    attr = pre_34_manips[old_type]
    object.xplane.manip.type_1050 = attr

# Function: update
# updates parts of the data model to ensure forward
# compatability between versions of XPlane2Blender
#
# Parameters:
#     fromVersion - The old version of the blender file
def update(fromVersion):
    if fromVersion <= '3.3.0':
        for scene in bpy.data.scenes:
            # set compositeTextures to False
            scene.xplane.compositeTextures = False

            if scene.xplane and scene.xplane.layers and len(scene.xplane.layers) > 0:
                for layer in scene.xplane.layers:
                    # set autodetectTextures to False
                    layer.autodetectTextures = False

                    # set export mode to cockpit, if cockpit was previously enabled
                    # TODO: Have users actually exported scenery objects before?
                    # Do we need to care about non-aircraft export types?
                    if layer.cockpit:
                        layer.export_type = 'cockpit'
                    else:
                        layer.export_type = 'aircraft'

    if fromVersion <= '3.4.0':
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                #Thanks to Python's duck typing and Blender's PointerProperties, this works
                __upgradeLocRot(bone)

        for object in bpy.data.objects:
            __upgradeLocRot(object)
            __upgradeManip(object)

@persistent
def load_handler(dummy):
    currentVersion = '.'.join(map(str,version))
    filepath = bpy.context.blend_data.filepath

    # do not update newly created files
    if not filepath:
        return

    fileVersion = bpy.data.scenes[0].get('xplane2blender_version','3.2.0')

    if fileVersion < currentVersion:
        #If it is a missing string we'll just call it '3.3.0' for some reason. I really don't get it.
        #-Ted 08/02/2017
        if len(fileVersion) == 0:
            fileVersion = '3.3.0'

        print('This file was created with an older XPlane2Blender version less than or equal to (%s) and will now automatically be updated to %s' % (fileVersion,currentVersion))

        update(fileVersion)

        bpy.data.scenes[0]['xplane2blender_version'] = currentVersion
        print('Your file was successfully updated to XPlane2Blender %s' % currentVersion)

bpy.app.handlers.load_post.append(load_handler)

@persistent
def save_handler(dummy):
    currentVersion = '.'.join(map(str,version))

    # store currentVersion
    bpy.data.scenes[0]['xplane2blender_version'] = currentVersion

bpy.app.handlers.save_pre.append(save_handler)

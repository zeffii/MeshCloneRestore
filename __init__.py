bl_info = {
    "name": "CloneRestore",
    "author": "Dealga McArdle",
    "version": (0, 2),
    "blender": (2, 7, 6),
    "location": "Object -> Tools -> Misc",
    "description": "clones and restores from clone",
    "warning": "20 Nov 2015",
    "wiki_url": "",
    "tracker_url": "",
    "category": "3D View"
}

import os
import json

import bpy
from bpy_extras.io_utils import ExportHelper


mode_set = bpy.ops.object.mode_set


def io_import():
    ctx = bpy.context
    ob, directory = ctx.active_object, ctx.scene.clone_io_directory

    full_path = os.path.join(directory, ob.name + '.json')
    with open(full_path) as ofile:
        text_str = ''.join(ofile.readlines())
        my_json = json.loads(text_str)
        verts, faces = my_json['verts'], my_json['faces']
        mesh = bpy.data.meshes.new(ob.name + "_clone")
        mesh.from_pydata(verts, [], faces)
        mesh.use_fake_user = True
        mesh.update()


def io_export():
    ctx = bpy.context
    ob, directory = ctx.active_object, ctx.scene.clone_io_directory

    full_path = os.path.join(directory, ob.name + '.json')
    with open(full_path, 'w') as ofile:

        verts = ob.data.vertices
        polygons = ob.data.polygons
        my_dict = {
            'verts': [v.co[:] for v in verts],
            'faces': [f.vertices[:] for f in polygons]
        }

        m = json.dumps(my_dict, sort_keys=True)
        ofile.write(m)


def clone():
    ob = bpy.context.active_object

    mode_set(mode='OBJECT')
    clone_mesh = ob.data.copy()
    clone_mesh.name = ob.name + '_clone'
    clone_mesh.use_fake_user = True

    mode_set(mode='EDIT')


def delete_clone():
    ob = bpy.context.active_object
    meshes = bpy.data.meshes

    if ob and (ob.name +  '_clone') in meshes:
        clone_name = ob.name +  '_clone'
        try:
            meshes.remove(meshes[clone_name])
            print('Mesh: {0} removed'.format(clone_name))
        except:
            print('failed to remove clone [ {0} ]..panic ! '.format(clone_name))


def restore():
    ob = bpy.context.active_object
    mode_set(mode='OBJECT')

    clone_mesh = bpy.data.meshes.get(ob.name + '_clone')
    clone_verts = clone_mesh.vertices
    for v in ob.data.vertices:
        if v.select:
            v.co = clone_verts[v.index].co

    mode_set(mode='EDIT')


def changed():
    ob = bpy.context.active_object
    bpy.ops.mesh.select_all(action='DESELECT')

    mode_set(mode='OBJECT')
    clone_mesh = bpy.data.meshes.get(ob.name + '_clone')
    clone_verts = clone_mesh.vertices
    for v in ob.data.vertices:
        if (v.co - clone_verts[v.index].co).length > 0.0001:
            v.select = True

    mode_set(mode='EDIT')


class ClonedRestoreOpsDirectorySelector(bpy.types.Operator, ExportHelper):
    bl_idname = "object.io_folder_selector"
    bl_label = "json folder"

    filename_ext = "."
    use_filter_folder = True

    def execute(self, context):
        # even if you pick a file i'll strip it and get the dirname
        fdir = self.properties.filepath
        dp = os.path.dirname(fdir)
        context.scene.clone_io_directory = dp
        return{'FINISHED'}


class ClonedRestoreOps(bpy.types.Operator):

    bl_idname = "object.cloned_restore_op"
    bl_label = "Short Name"

    fn_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        if self.fn_name in {'io_import', 'io_export'}:
            if not os.path.isdir(context.scene.clone_io_directory):
                return {'CANCELLED'}

        exec(self.fn_name + '()')
        return {'FINISHED'}


class ClonedRestore(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Clone Restore Panel"
    bl_idname = "OBJECT_PT_clone_restore"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        ob = context.active_object
        scn = context.scene
        op_dispatch = "object.cloned_restore_op"
        operators = 'clone', 'restore', 'changed'

        clone_is_present = bool(ob) and (ob.name + '_clone' in bpy.data.meshes)
        
        if clone_is_present:
            opdel = 'delete_clone'
            col.operator(op_dispatch, text=opdel, icon='CANCEL').fn_name = opdel

        for op in operators:
            if op == 'clone' and clone_is_present:
                col.label('cloned as: ' + ob.name + '_clone')
            else:
                col.operator(op_dispatch, text=op).fn_name = op

        col.label('I / O')

        row = col.row(align=True)
        row.prop(scn, 'clone_io_directory', text='directory:')
        row.operator("object.io_folder_selector", icon="FILE_FOLDER", text="")

        col.operator("object.cloned_restore_op", text='import').fn_name = 'io_import'
        col.operator("object.cloned_restore_op", text='export').fn_name = 'io_export'


def register():
    bpy.types.Scene.clone_io_directory = bpy.props.StringProperty()
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
    del bpy.types.Scene.clone_io_directory


if __name__ == "__main__":
    register()

bl_info = {
    "name": "Focus on Mouse",
    "description": "Focus view on mouse",
    "author": "A Nakanosora",
    "version": (0, 4, 0),
    "blender": (2, 77, 0),
    "location": "Default Hotkey: Shift+Ctrl+Q  (Input -> 3D View -> Focus on Mouse)",
    "warning": "",
    "category": "3D View"
    }

import bpy
import bpy_extras
from mathutils import Vector, Matrix
import math
import time

class ModalState():pass

def on_modal_tween(context, event, modal_state):
    hitloc = modal_state.hitloc
    loc0 = modal_state.loc0
    t = modal_state.t

    p = loc0 + (hitloc-loc0)*t
    focus_view_on(context.space_data.region_3d, p)

    if t >= 1.0:
        return {'FINISHED'}
    return {'RUNNING_MODAL'}

def focus_view_on(region_3d, location):
    r3d = region_3d

    a = r3d.view_location.copy()
    b = location
    mm = r3d.view_matrix.inverted()

    vr = mm.to_3x3()
    loc = mm.translation

    n = (a-loc).cross(b-loc).normalized()
    alp = math.acos( max(-1.0,min(1.0,  (a-loc).normalized().dot( (b-loc).normalized() )  )))

    zero = Vector()
    u0,v0,w0 = vr.transposed()
    u = rot_on( zero, n, alp, u0 )
    v = rot_on( zero, n, alp, v0 )
    w = rot_on( zero, n, alp, w0 )

    if bpy.context.user_preferences.inputs.view_rotate_method == 'TURNTABLE':
        ez = Vector((0,0,1))
        u2 = ez.cross(w)
        v2 = w.cross(u2)
        u,v = u2,v2

    vr2 = Matrix((u,v,w)).transposed()

    mm2 = vr2.to_4x4()
    mm2[0][3] = loc[0]
    mm2[1][3] = loc[1]
    mm2[2][3] = loc[2]

    dist0 = (loc-location).length
    r3d.view_distance = dist0
    r3d.view_matrix = mm2.inverted()

def rot_on(p, n, theta, a):
    r = a-p
    r_new = n*n.dot(r) + (r-n*n.dot(r))*math.cos(theta) - r.cross(n)*math.sin(theta)
    b = p+r_new
    return b

def get_nearest_object_under_mouse(context, event, ray_max=1000.0):
    import bpy
    from bpy_extras import view3d_utils

    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    ray_target = ray_origin + (view_vector * ray_max)

    def visible_objects_and_duplis():
        for obj in context.visible_objects:
            if obj.type == 'MESH':
                yield (obj, obj.matrix_world.copy())

            if obj.dupli_type != 'NONE':
                obj.dupli_list_create(scene)
                for dob in obj.dupli_list:
                    obj_dupli = dob.object
                    if obj_dupli.type == 'MESH':
                        yield (obj_dupli, dob.matrix.copy())

            obj.dupli_list_clear()

    def obj_ray_cast(obj, matrix):
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv * ray_origin
        ray_target_obj = matrix_inv * ray_target
        ray_direction_obj = ray_target_obj - ray_origin_obj
        success, location, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj)

        if success:
            return location, normal, face_index
        else:
            return None, None, None

    best_length_squared = ray_max * ray_max
    best_hit_coord = None
    best_obj = None
    best_obj_face_index = None

    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH':
            try:
                hit, normal, face_index = obj_ray_cast(obj, matrix)
            except:
                try:
                    bpy.ops.object.editmode_toggle()
                    hit, normal, face_index = obj_ray_cast(obj, matrix)
                    bpy.ops.object.editmode_toggle()
                except:
                    hit, normal, face_index = None, None, None

            if hit is not None:
                hit_world = matrix * hit
                length_squared = (hit_world - ray_origin).length_squared
                if length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj
                    best_obj_face_index = face_index
                    best_hit_coord = hit_world
    return best_hit_coord, best_obj, best_obj_face_index

class FocusMouseOperator(bpy.types.Operator):
    bl_idname = "view3d.focus_on_mouse"
    bl_label = "Focus on Mouse"

    _timer = None
    _t0 = -1
    _TWEEN_TIME = 0.2
    _modal_state = None

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        current_view_type = context.space_data.region_3d.view_perspective
        if current_view_type == 'PERSP':
            if self._modal_state is not None:
                return {'CANCELLED'}

            if context.space_data.type != 'VIEW_3D':
                self.report({'WARNING'}, "Active space must be a View3d")
                return {'CANCELLED'}

            hitloc, _, _ = get_nearest_object_under_mouse(context, event)
            if hitloc is None:
                return {'CANCELLED'}

            r3d = context.space_data.region_3d
            self._modal_state = ModalState()
            self._modal_state.hitloc = hitloc
            self._modal_state.loc0 = r3d.view_location.copy()
            self.t = 0.0

            self._timer = context.window_manager.event_timer_add(0.01, context.window)
            self._t0 = time.time()
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        elif current_view_type == 'ORTHO':
            bpy.ops.view3d.view_center_pick('INVOKE_DEFAULT')
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            t1 = time.time()
            t = min(1.0, (t1-self._t0)/self._TWEEN_TIME)
            self._modal_state.t = t

            try:
                res = on_modal_tween(context, event, self._modal_state)
                if res in [{'CANCELLED'}, {'FINISHED'}]:
                    self.cancel(context)
                return res
            except Exception as e:
                self.report({'WARNING'}, "Error on modal")
                print(e)
                self.cancel(context)
                return {'CANCELLED'}

        else:
            return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self._modal_state = None
        self._t0 = -1
        self._timer = None
        return {'CANCELLED'}

def bind_hotkey():
    km = bpy.context.window_manager.keyconfigs.active.keymaps['3D View']
    km.keymap_items.new(FocusMouseOperator.bl_idname, 'Q', 'PRESS', ctrl=True, shift=True)

def unbind_hotkey():
    km = bpy.context.window_manager.keyconfigs.active.keymaps['3D View']
    for kmi in km.keymap_items:
        if kmi.idname == FocusMouseOperator.bl_idname:
            km.keymap_items.remove(kmi)

def register():
    bpy.utils.register_class(FocusMouseOperator)
    bind_hotkey()

def unregister():
    bpy.utils.unregister_class(FocusMouseOperator)
    unbind_hotkey()

if __name__ == '__main__':
    register()
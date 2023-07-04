from metavision_sdk_core import PeriodicFrameGenerationAlgorithm
from metavision_sdk_ui import EventLoop, BaseWindow, Window, UIAction, UIKeyEvent

mv_iterator = EventsIterator(input_path=args.input_path, delta_t=1000)
height, width = mv_iterator.get_size()  # Camera Geometry

# Window - Graphical User Interface
with Window(title="Metavision SDK Get Started", width=width, height=height, mode=BaseWindow.RenderMode.BGR) as window:
    def keyboard_cb(key, scancode, action, mods):
        if action != UIAction.RELEASE:
            return
        if key == UIKeyEvent.KEY_ESCAPE or key == UIKeyEvent.KEY_Q:
            window.set_close_flag()

    window.set_keyboard_callback(keyboard_cb)

# Event Frame Generator
event_frame_gen = PeriodicFrameGenerationAlgorithm(sensor_width=width, sensor_height=height,
                                                   accumulation_time_us=accumulation_time_us)

def on_cd_frame_cb(ts, cd_frame):
    window.show(cd_frame)

event_frame_gen.set_output_callback(on_cd_frame_cb)

# Process events
for evs in mv_iterator:
    # Dispatch system events to the window
    EventLoop.poll_and_dispatch()

    event_frame_gen.process_events(evs)
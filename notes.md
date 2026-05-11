daniel@fedora:~/Desktop/demo$ python game.py
pygame-ce 2.5.7 (SDL 2.32.10, Python 3.14.3)
Traceback (most recent call last):
File "/home/daniel/Desktop/demo/game.py", line 1037, in <module>
main()
~~~~^^
File "/home/daniel/Desktop/demo/game.py", line 1034, in main
Game().run()
~~~~~~~~~~^^
File "/home/daniel/Desktop/demo/game.py", line 166, in run
self.main_menu()
~~~~~~~~~~~~~~^^
File "/home/daniel/Desktop/demo/game.py", line 174, in main_menu
menu_result: str | None = self.start_game_from_menu()
~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/daniel/Desktop/demo/game.py", line 198, in start_game_from_menu
if result == "continue": result = self.first_scene_obj.run()
~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/daniel/Desktop/demo/scripts/scenes/first_scene.py", line 200, in run
self.render_bed_sleep_prompt(dt)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^
File "/home/daniel/Desktop/demo/scripts/scenes/first_scene.py", line 1004, in render_bed_sleep_prompt
target_alpha = 255 if self.is_near_bed() else 0
~~~~~~~~~~~~~~~~^^
File "/home/daniel/Desktop/demo/scripts/scenes/first_scene.py", line 988, in is_near_bed
if self.flags["bed_sleep_done"]: return False
~~~~~~~~~~^^^^^^^^^^^^^^^^^^
KeyError: 'bed_sleep_done'

for the panicked breathing, i want the last breaths to continue while the heartbeat gets faster and faster, please show the heartbeat bpm icon on the top middle of the screen.

i still cant hear my bpm/heartbeat nor can i hear my speech sound sfx.

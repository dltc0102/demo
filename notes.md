okay i think there are some limits for how far up and how far down ghosts can spawn and move to. ill make a few polygons of what the possible areas for moving in are for the bedroom and the kitchen: if bottom left point of ghost + ghost width iss >= 720, make sure they can't get past 720 - ghost width - 2 ssame for the left side: if bottom left point of ghost <= 2, make sure their x is 2. 2 from the left and right is the minimal padding. bedroom_floor: [(1, 438), (364, 434), (420, 423), (563, 423), (718, 423), (718, 533), (1, 533)] bedroom_bed: [(151, 363), (190, 351), (409, 357), (363, 370)] shelf_1: [(54, 142), (204, 142)] shelf_2: [(557, 295), (706, 296)] shelf_3: [(623, 238), (702, 237)] also it would dbe cool if a ghost spawned on shelf 2, but dropped ddown to shelf 3. or was on shelf 1 andd dropped ddown to bedroom_bedd. or from beddroom_bed dropped down to bedroom_floor. but ghosts cant move up. only down. now for the polygon points in the kitchen: remember the 2px padding for each side, for kitchen we would need to do it in world points. kitchen_floor: [(2, 357), (119*, 361), (130*, 366), (433*, 360), (642*, 457), (718, 450), (718, 545), (2, 545)] but for kitchen floor, note that there's an island in the midddle that the ghost can't walk inside. that island_polygon is: [(154, 363), (411*, 360), (413*, 471), (184, 471), (155, 437)] now for the other fun areas a ghost can move on in the kitchen: above_the_fridge: [(565, 136), (641, 132), (718*, 129)] cupboard1: [(129, 98), (212*, 105)] cupboard2: [(338, 96), (467, 98), (608*, 85)] island_top: [(155, 303), (367*, 301), (412*, 331), (185, 334)] sink_top: [(128, 270), (495*, 264)] sink_top2: [(495*, 264), (554*, 287)] note if the list of points are less than 4, they are lines or paths a ghost can take. note if there is a \* next to the number, it meanss that the x point is the number - ghost width when ghosts talk, they should not have speech_sfx. tell me what other file you would want.

and i also feel like the sounds are muted somehow. after player goes into kitchen, the voices work but sounds like walking on wood, or walking on tiless, or even the heartbeat, fridge open, fridge close, pouring milk, they all dont work. also for that liar liar area, the voices are sspeakingall at the same time which is not correct. another note. bedroom <- should only show if player has seen the sticky note and has gotten milk and voice has played "why_are_you_so_slow" also ive said this before, maybe not to you, but: self.script.play_voice methods cannot be in a yield from itertools.chain() loop. they have to be outside with a yield from. this is because of how itertools.chain() workss where arguments are processed before methodds and so the voices are played at the same time.

- i havent even interacted with the fridge yet, why is it pulsing for bedroom? that's misleading. bedroom <- should only show if player has seen the sticky note and has gotten milk and voice has played "why_are_you_so_slow" and fridge has been interacted with, and player is holding a glass of milk.

- when the player fails an attempt and a sound is being played, wait until the voice is finished dbeing played before the think methods, the say methods and the voice methods are played.

- when the player fails an attempt, let the circle for the progress of attempting to get milk stall and turn red with an error like shake.

- whenever a player fails an attempt, the heart beat should increase by 15 increments of bpm every time and teh heartbeats should become increasingly loud.

- remove the "nizenmehaimeishuine" dialogue

- if the sticky note has not been read yet, and the sticky note needs to be read, it currently just shines bright. instead, of that, could you make it pulse too? signalling that it needs to be opened and read.

- also after the player drinks milk, instead of the screen fading to black, the game crashes:
  here is the traceback:
  daniel@fedora:~/Desktop/demo$ python game.py
  pygame-ce 2.5.7 (SDL 2.32.10, Python 3.14.3)
  Traceback (most recent call last):
  File "/home/daniel/Desktop/demo/game.py", line 1151, in <module>
  main()
  ```^^
  File "/home/daniel/Desktop/demo/game.py", line 1148, in main
  Game().run()
  ~~~~~~~~~~^^
  File "/home/daniel/Desktop/demo/game.py", line 186, in run
  self.main_menu()
  ~~~~~~~~~~~~~~^^
  File "/home/daniel/Desktop/demo/game.py", line 195, in main_menu
  menu_result: str | None = self.start_game_from_menu()
  ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/daniel/Desktop/demo/game.py", line 219, in start_game_from_menu
  if result == "continue": result = self.first_scene_obj.run()
  ~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/daniel/Desktop/demo/scripts/scenes/first_scene.py", line 273, in run
  self.game.cutscene.update()
  ~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/home/daniel/Desktop/demo/scripts/core/cutscene_engine.py", line 68, in update
  result = next(self.sequence)
  File "/home/daniel/Desktop/demo/scripts/scenes/first_scene.py", line 484, in go_to_bed
  yield from itertools.chain(
  ...<5 lines>...
  )
  TypeError: 'pygame.mixer.Channel' object is not iterable
  ```

here are my current files fo ryou to have references and make eddits to:

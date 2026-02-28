import arcade
import json
import os

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 750
CAMERA_LERP = 0.12
TILE_SIZE = 16

SCREEN_TITLE = "Лабиринт"
SAVE_FILE = "save.json"
FON_FILE = "fon.png"
MUSIC_FILE = "music.MP3"

background_music = None
music_play = None
music_playing = False


class MainWindow(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(FON_FILE)

        self.new_game_btn = None
        self.load_game_btn = None

    def on_show_view(self):
        global background_music, music_play, music_playing
        if music_play is not None:
            background_music.stop(music_play)
            music_play = None
            music_playing = False

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        arcade.draw_text("Добро пожаловать в Лабиринт", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                         arcade.color.WHITE, font_size=50, anchor_x="center")

        btn_w = 300
        btn_h = 60
        btn_x = SCREEN_WIDTH / 2
        btn_y1 = SCREEN_HEIGHT / 2
        btn_y2 = SCREEN_HEIGHT / 2 - 80

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y1 - btn_h/2, btn_w, btn_h, arcade.color.GREEN)
        arcade.draw_text("НОВАЯ ИГРА", btn_x, btn_y1,
                         arcade.color.BLACK, font_size=24, anchor_x="center", anchor_y="center")

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y2 - btn_h/2, btn_w, btn_h, arcade.color.ORANGE)
        arcade.draw_text("ЗАГРУЗИТЬ ИГРУ", btn_x, btn_y2,
                         arcade.color.BLACK, font_size=24, anchor_x="center", anchor_y="center")

        self.new_game_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y1 - btn_h/2, btn_y1 + btn_h/2)
        self.load_game_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y2 - btn_h/2, btn_y2 + btn_h/2)

    def on_mouse_press(self, x, y, button, modifiers):
        if (self.new_game_btn[0] <= x <= self.new_game_btn[1] and
                self.new_game_btn[2] <= y <= self.new_game_btn[3]):
            level_view = LVL1()
            level_view.setup()
            self.window.show_view(level_view)

        if (self.load_game_btn[0] <= x <= self.load_game_btn[1] and
                self.load_game_btn[2] <= y <= self.load_game_btn[3]):
            load_view = LoadWindow()
            load_view.setup()
            self.window.show_view(load_view)


class SampleLVLWindow(arcade.View):
    def __init__(self, level_number, start_x=None, start_y=None):
        super().__init__()
        self.LVL = level_number
        self.start_x = start_x
        self.start_y = start_y
        self.player_speed = 30

        self.world_camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()

        self.floor_list = arcade.SpriteList()
        self.decor1_list = arcade.SpriteList()
        self.decor2_list = arcade.SpriteList()
        self.decor3_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.key_list = arcade.SpriteList()
        self.exit_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.hitbox_list = arcade.SpriteList()

        self.player_sprite = None
        self.keys_collected = 0
        self.exit_open = False
        self.pause = False

    def setup(self):
        arcade.set_background_color(arcade.color.BLACK)

        global background_music, music_play, music_playing
        if not music_playing:
            background_music = arcade.Sound(MUSIC_FILE, streaming=True)
            music_play = background_music.play(volume=0.5, loop=True)
            music_playing = True

        self.tile_map = arcade.load_tilemap(f"maps\\map{self.LVL}.tmx", TILE_SIZE)

        self.floor_list = self.tile_map.sprite_lists.get("floor", arcade.SpriteList())
        self.decor1_list = self.tile_map.sprite_lists.get("decor", arcade.SpriteList())
        self.decor2_list = self.tile_map.sprite_lists.get("decor 2", arcade.SpriteList())
        self.decor3_list = self.tile_map.sprite_lists.get("decor 3", arcade.SpriteList())
        self.wall_list = self.tile_map.sprite_lists.get("wall", arcade.SpriteList())
        self.hitbox_list = self.tile_map.sprite_lists.get("hitbox", arcade.SpriteList())
        self.key_list = self.tile_map.sprite_lists.get("key", arcade.SpriteList())
        self.exit_list = self.tile_map.sprite_lists.get("exit", arcade.SpriteList())

        self.map_width = self.tile_map.width * TILE_SIZE
        self.map_height = self.tile_map.height * TILE_SIZE

        self.player_sprite = arcade.Sprite("player.png", scale=1.0)

        self.player_list.append(self.player_sprite)

        self.player_sprite.center_x = self.start_x
        self.player_sprite.center_y = self.start_y

        self.world_camera.position = (self.player_sprite.center_x, self.player_sprite.center_y)
        self.world_camera.zoom = 0.2

    def on_draw(self):
        self.clear()

        if not self.pause:
            self.world_camera.use()

            self.floor_list.draw()
            self.decor1_list.draw()
            self.player_list.draw()
            self.wall_list.draw()
            self.decor2_list.draw()
            self.decor3_list.draw()
            self.key_list.draw()
            self.exit_list.draw()

            self.gui_camera.use()
            self.info()

    def save_game(self):
        save_data = {
            'level': self.LVL,
            'player_x': self.player_sprite.center_x,
            'player_y': self.player_sprite.center_y,
            'keys_collected': self.keys_collected,
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(save_data, f, indent=4)

    def load_save(self, save_data):
        self.LVL = save_data['level']
        self.keys_collected = save_data['keys_collected']
        self.player_sprite.center_x = save_data['player_x']
        self.player_sprite.center_y = save_data['player_y']
        self.exit_open = (self.keys_collected >= 3)

    def info(self):
        key_text = f"🔑{self.keys_collected}/3"

        if self.keys_collected >= 3:
            color = arcade.color.GREEN
        else:
            color = arcade.color.GOLD
        arcade.draw_text(key_text,
                         SCREEN_WIDTH - 75, SCREEN_HEIGHT - 30,
                         color, font_size=24,
                         anchor_x="center", anchor_y="center")
        arcade.draw_lbwh_rectangle_outline(SCREEN_WIDTH - 120, SCREEN_HEIGHT - 50,
                                           100, 40, arcade.color.WHITE, 2)
        arcade.draw_text(f"Уровень: {self.LVL}/3",
                         10, SCREEN_HEIGHT - 30,
                         arcade.color.WHITE, font_size=16)

        if self.keys_collected >= 3:
            arcade.draw_text("ДВЕРЬ ОТКРЫТА!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50,
                             arcade.color.GREEN, font_size=20,
                             anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            pause_view = PauseWindow(self)
            self.window.show_view(pause_view)
        if not self.pause:
            if key in (arcade.key.LEFT, arcade.key.A):
                self.player_sprite.change_x = -self.player_speed
            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player_sprite.change_x = self.player_speed
            elif key in (arcade.key.UP, arcade.key.W):
                self.player_sprite.change_y = self.player_speed
            elif key in (arcade.key.DOWN, arcade.key.S):
                self.player_sprite.change_y = -self.player_speed

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
            self.player_sprite.change_x = 0
        if key in (arcade.key.UP, arcade.key.DOWN, arcade.key.W, arcade.key.S):
            self.player_sprite.change_y = 0

    def update_player(self):
        old_x = self.player_sprite.center_x
        old_y = self.player_sprite.center_y

        self.player_sprite.center_x += self.player_sprite.change_x
        if arcade.check_for_collision_with_list(self.player_sprite, self.hitbox_list):
            self.player_sprite.center_x = old_x

        self.player_sprite.center_y += self.player_sprite.change_y
        if arcade.check_for_collision_with_list(self.player_sprite, self.hitbox_list):
            self.player_sprite.center_y = old_y

    def on_update(self, delta_time):
        if not self.pause:
            self.update_player()

            keys_hit = arcade.check_for_collision_with_list(self.player_sprite, self.key_list)
            for key in keys_hit:
                key.remove_from_sprite_lists()
                self.keys_collected += 1

            if self.keys_collected >= 3 and not self.exit_open:
                self.exit_open = True

            if self.exit_open:
                exit_hit = arcade.check_for_collision_with_list(self.player_sprite, self.exit_list)
                if exit_hit:
                    complete_view = LVLFinish(self.LVL)
                    self.window.show_view(complete_view)

            target = (self.player_sprite.center_x, self.player_sprite.center_y)
            self.world_camera.position = arcade.math.lerp_2d(
                self.world_camera.position,
                target,
                CAMERA_LERP,
            )


class LVL1(SampleLVLWindow):
    def __init__(self):
        super().__init__(1, 1440, 1440)


class LVL2(SampleLVLWindow):
    def __init__(self):
        super().__init__(2, 4400, 7000)


class LVL3(SampleLVLWindow):
    def __init__(self):
        super().__init__(3, 3900, 4400)


class PauseWindow(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.texture = arcade.load_texture(FON_FILE)

        self.game_view = game_view
        self.resume_btn = None
        self.save_btn = None
        self.menu_btn = None
        self.exit_btn = None

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, (0, 0, 0, 200))
        arcade.draw_text("ПАУЗА", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 200,
                         arcade.color.WHITE, font_size=50, anchor_x="center")

        btn_w = 300
        btn_h = 60
        btn_x = SCREEN_WIDTH / 2
        btn_y1 = SCREEN_HEIGHT / 2 + 100
        btn_y2 = SCREEN_HEIGHT / 2 + 20
        btn_y3 = SCREEN_HEIGHT / 2 - 60
        btn_y4 = SCREEN_HEIGHT / 2 - 140

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y1 - btn_h/2, btn_w, btn_h, arcade.color.GREEN)
        arcade.draw_text("ВЕРНУТЬСЯ", btn_x, btn_y1,
                         arcade.color.BLACK, font_size=20, anchor_x="center", anchor_y="center")
        self.resume_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y1 - btn_h/2, btn_y1 + btn_h/2)

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y2 - btn_h/2, btn_w, btn_h, arcade.color.BLUE)
        arcade.draw_text("СОХРАНИТЬ", btn_x, btn_y2,
                         arcade.color.WHITE, font_size=20, anchor_x="center", anchor_y="center")
        self.save_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y2 - btn_h/2, btn_y2 + btn_h/2)

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y3 - btn_h/2, btn_w, btn_h, arcade.color.ORANGE)
        arcade.draw_text("ГЛАВНОЕ МЕНЮ", btn_x, btn_y3,
                         arcade.color.BLACK, font_size=20, anchor_x="center", anchor_y="center")
        self.menu_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y3 - btn_h/2, btn_y3 + btn_h/2)

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y4 - btn_h/2, btn_w, btn_h, arcade.color.RED)
        arcade.draw_text("СОХРАНИТЬ И ВЫЙТИ", btn_x, btn_y4,
                         arcade.color.WHITE, font_size=20, anchor_x="center", anchor_y="center")
        self.exit_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y4 - btn_h/2, btn_y4 + btn_h/2)

    def on_mouse_press(self, x, y, button, modifiers):
        if (self.resume_btn[0] <= x <= self.resume_btn[1] and
                self.resume_btn[2] <= y <= self.resume_btn[3]):
            self.window.show_view(self.game_view)

        if (self.save_btn[0] <= x <= self.save_btn[1] and
                self.save_btn[2] <= y <= self.save_btn[3]):
            self.game_view.save_game()

            self.window.show_view(self.game_view)
        if (self.menu_btn[0] <= x <= self.menu_btn[1] and
                self.menu_btn[2] <= y <= self.menu_btn[3]):
            menu_view = MainWindow()
            self.window.show_view(menu_view)

        if (self.exit_btn[0] <= x <= self.exit_btn[1] and
                self.exit_btn[2] <= y <= self.exit_btn[3]):
            self.game_view.save_game()
            arcade.exit()


class LVLFinish(arcade.View):
    def __init__(self, level_completed):
        super().__init__()
        self.texture = arcade.load_texture(FON_FILE)

        self.level_completed = level_completed
        self.next_level_btn = None
        self.menu_btn = None
        self.save_btn = None

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.level_completed == 3:
            arcade.draw_text("ВЫ ПРОШЛИ ВСЕ УРОВНИ!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                             arcade.color.GOLD, font_size=40, anchor_x="center")
        else:
            arcade.draw_text(f"Уровень {self.level_completed} пройден!",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                             arcade.color.GOLD, font_size=40, anchor_x="center")

        btn_w = 300
        btn_h = 60
        btn_x = SCREEN_WIDTH / 2

        if self.level_completed < 3:
            btn_y1 = SCREEN_HEIGHT / 2 + 50
            arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y1 - btn_h/2, btn_w, btn_h, arcade.color.BLUE)
            arcade.draw_text("СЛЕДУЮЩИЙ УРОВЕНЬ", btn_x, btn_y1,
                             arcade.color.WHITE, font_size=20, anchor_x="center", anchor_y="center")
            self.next_level_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y1 - btn_h/2, btn_y1 + btn_h/2)

        btn_y2 = SCREEN_HEIGHT / 2 - 20
        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y2 - btn_h/2, btn_w, btn_h, arcade.color.GREEN)
        arcade.draw_text("СОХРАНИТЬ", btn_x, btn_y2,
                         arcade.color.BLACK, font_size=20, anchor_x="center", anchor_y="center")
        self.save_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y2 - btn_h/2, btn_y2 + btn_h/2)

        if self.level_completed >= 3:
            btn_y3 = SCREEN_HEIGHT / 2 - 20
        else:
            btn_y3 = SCREEN_HEIGHT / 2 - 90

        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y3 - btn_h/2, btn_w, btn_h, arcade.color.RED)
        arcade.draw_text("ГЛАВНОЕ МЕНЮ", btn_x, btn_y3,
                         arcade.color.WHITE, font_size=20, anchor_x="center", anchor_y="center")
        self.menu_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y3 - btn_h/2, btn_y3 + btn_h/2)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.next_level_btn and self.level_completed < 3:
            if (self.next_level_btn[0] <= x <= self.next_level_btn[1] and
                    self.next_level_btn[2] <= y <= self.next_level_btn[3]):
                if self.level_completed == 1:
                    next_view = LVL2()
                else:
                    next_view = LVL3()
                next_view.setup()
                self.window.show_view(next_view)

        if self.save_btn:
            if (self.save_btn[0] <= x <= self.save_btn[1] and
                    self.save_btn[2] <= y <= self.save_btn[3]):
                if self.level_completed == 1:
                    save_view = LVL2()
                elif self.level_completed == 2:
                    save_view = LVL3()
                else:
                    save_view = LVL1()
                save_view.setup()
                save_view.keys_collected = 0
                save_view.save_game()
                menu_view = MainWindow()
                self.window.show_view(menu_view)

        if (self.menu_btn[0] <= x <= self.menu_btn[1] and
                self.menu_btn[2] <= y <= self.menu_btn[3]):
            menu_view = MainWindow()
            self.window.show_view(menu_view)


class LoadWindow(arcade.View):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture(FON_FILE)

        self.load_btn = None
        self.back_btn = None
        self.save = False
        self.data = None

    def setup(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                self.data = json.load(f)
                self.save = True
        else:
            self.save = False

    def on_draw(self):
        self.clear()

        arcade.draw_texture_rect(self.texture,
                                 arcade.rect.XYWH(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT))

        arcade.draw_text("ЗАГРУЗКА ИГРЫ", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150,
                         arcade.color.WHITE, font_size=50, anchor_x="center")

        btn_w = 300
        btn_h = 60
        btn_x = SCREEN_WIDTH / 2

        if self.save:
            level = self.data['level']
            keys = self.data['keys_collected']
            arcade.draw_text(f"Сохранение: Уровень {level}, ключей {keys}/3",
                             SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                             arcade.color.WHITE, font_size=24, anchor_x="center")

            btn_y1 = SCREEN_HEIGHT / 2 - 30
            arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y1 - btn_h/2, btn_w, btn_h, arcade.color.GREEN)
            arcade.draw_text("ЗАГРУЗИТЬ", btn_x, btn_y1,
                             arcade.color.BLACK, font_size=24, anchor_x="center", anchor_y="center")
            self.load_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y1 - btn_h/2, btn_y1 + btn_h/2)
        else:
            arcade.draw_text("Сохранений не найдено", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50,
                             arcade.color.WHITE, font_size=24, anchor_x="center")

        btn_y2 = SCREEN_HEIGHT / 2 - 120
        arcade.draw_lbwh_rectangle_filled(btn_x - btn_w/2, btn_y2 - btn_h/2, btn_w, btn_h, arcade.color.RED)
        arcade.draw_text("НАЗАД", btn_x, btn_y2,
                         arcade.color.WHITE, font_size=24, anchor_x="center", anchor_y="center")
        self.back_btn = (btn_x - btn_w/2, btn_x + btn_w/2, btn_y2 - btn_h/2, btn_y2 + btn_h/2)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.save and self.load_btn:
            if (self.load_btn[0] <= x <= self.load_btn[1] and
                    self.load_btn[2] <= y <= self.load_btn[3]):
                level = self.data['level']
                if level == 1:
                    game_view = LVL1()
                elif level == 2:
                    game_view = LVL2()
                else:
                    game_view = LVL3()
                game_view.setup()
                game_view.load_save(self.data)
                self.window.show_view(game_view)

        if (self.back_btn[0] <= x <= self.back_btn[1] and
                self.back_btn[2] <= y <= self.back_btn[3]):
            menu_view = MainWindow()
            self.window.show_view(menu_view)


def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    menu_view = MainWindow()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()
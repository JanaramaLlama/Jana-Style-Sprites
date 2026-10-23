import random
from re import sub

import i18n

import scripts.game_structure.screen_settings
from scripts.cat.enums import CatAge
from scripts.cat.sprites.load_sprites import sprites
from scripts.game_structure import constants
from scripts.game_structure.localization import get_lang_config
from scripts.events_module.text_adjust import adjust_list_text


class Pelt:
    """Holds all appearance information for a cat."""

    # SHARED DATA

    # SCARS
    # bite scars by @wood pank on discord
    general_scars = []
    missing_part_scars = []
    for sprite_list in sprites.SCAR_DATA["sprite_list"]:
        if sprite_list == sprites.SCAR_DATA["sprite_list"][-1]:
            missing_part_scars.extend(sprite_list)
        else:
            general_scars.extend(sprite_list)

    all_scars = [general_scars + missing_part_scars]

    # ACCESSORIES
    # make sure to add plural and singular forms of new accs to accessories.en.json so that they will display nicely

    # all acc sprites are labeled as occupying a specific part of the cat sprite and then appended into these three lists
    # collar_accessories are presumed to all occupy the neck area and are treated as the fourth of these lists
    tail_accessories = []
    body_accessories = []
    head_accessories = []
    paw_accessories = []

    # here we create the master lists of each accessory type
    plant_accessories = []
    for sprite_list in sprites.PLANT_DATA["sprite_list"]:
        plant_accessories.extend(sprite_list)
        for sprite in sprite_list:
            if sprite_list[sprite] == "tail":
                tail_accessories.append(sprite)
            elif sprite_list[sprite] == "body":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "head":
                head_accessories.append(sprite)
            elif sprite_list[sprite] == "paw":
                paw_accessories.append(sprite)

    wild_accessories = []
    for sprite_list in sprites.WILD_DATA["sprite_list"]:
        wild_accessories.extend(sprite_list)
        for sprite in sprite_list:
            if sprite_list[sprite] == "tail":
                tail_accessories.append(sprite)
            elif sprite_list[sprite] == "body":
                body_accessories.append(sprite)
            elif sprite_list[sprite] == "head":
                head_accessories.append(sprite)
            elif sprite_list[sprite] == "paw":
                paw_accessories.append(sprite)

    collar_accessories = []
    collar_styles = []
    if sprites.COLLAR_DATA["palette_map"]:
        for style_type in sprites.COLLAR_DATA["style_data"]:
            for style, color_list in style_type.items():
                collar_styles.append(style)
                for colour in color_list:
                    collar_accessories.append(f"{style}_{colour}")
    else:
        for sprite_list in sprites.COLLAR_DATA["sprite_list"]:
            collar_accessories.extend(sprite_list)

    # this is used for acc-giving events, only change if you're adding a new category tag to the event filter
    # adding a category here will automatically update the event editor's options
    acc_categories = {
        "PLANT": plant_accessories,
        "WILD": wild_accessories,
        "COLLAR": collar_accessories,
    }

    def __init__(
        self,
        name: str = "SingleColour",
        length: str = "short",
        colour: str = "WHITE",
        white_patches: str = None,
        eye_color: str = "BLUE",
        eye_colour2: str = None,
        tortie_base: str = None,
        tortie_colour: str = None,
        tortie_marking: str = None,
        tortie_pattern: str = None,
        vitiligo: str = None,
        points: str = None,
        accessory: list = None,
        paralyzed: bool = False,
        opacity: int = 100,
        scars: list = None,
        tint: str | None = None,
        skin: str = "BLACK",
        white_patches_tint: str | None = None,
        newborn_sprite: str = None,
        kitten_sprite: str = None,
        adol_sprite: str = None,
        adult_sprite: str = None,
        senior_sprite: str = None,
        para_adult_sprite: str = None,
        para_adolescent_sprite: str = None,
        para_kitten_sprite: str = None,
        reverse: bool = False,
        sps_index: int = 1,
    ) -> None:
        self.name = name
        self.colour = colour
        self.white_patches = white_patches
        self.eye_colour = eye_color
        self.eye_colour2 = eye_colour2
        self.tortie_base = tortie_base
        self.tortie_marking = tortie_marking
        self.tortie_pattern = tortie_pattern
        self.tortie_colour = tortie_colour
        self.vitiligo = vitiligo
        self.length = length
        self.points = points
        self.rebuild_sprite = True
        self._accessory = accessory
        self._paralyzed = paralyzed
        self.opacity = opacity
        self._scars = (
            tuple(scars)
            if isinstance(scars, list)
            else scars
            if isinstance(scars, tuple)
            else tuple()
        )
        self.tint = tint
        self.white_patches_tint = white_patches_tint
        self.screen_scale = scripts.game_structure.screen_settings.screen_scale
        self.reverse = reverse
        self.skin = skin
        self._sps_index = sps_index

        if not getattr(Pelt, "fur_length", None):
            self._init_data()

        fur_length = "short"

        # converting old pose numbers into names
        if any(
            isinstance(x, int) or x is None
            for x in [
                newborn_sprite,
                kitten_sprite,
                adol_sprite,
                adult_sprite,
                senior_sprite,
                para_adult_sprite,
                para_adolescent_sprite,
                para_kitten_sprite,
            ]
        ):
            # DO NOT CHANGE THIS: this is meant to convert old saves and should not be updated with new pose additions
            self.cat_sprites = {
                "kitten": kitten_sprite if kitten_sprite is not None else 0,
                "adolescent": adol_sprite if adol_sprite is not None else 3,
                "young adult": adult_sprite if adult_sprite is not None else 6,
                "adult": adult_sprite if adult_sprite is not None else 6,
                "senior adult": adult_sprite if adult_sprite is not None else 6,
                "senior": senior_sprite if senior_sprite is not None else 12,
                "para_adult": para_adult_sprite,
                "newborn": 20,
            }
            for age, pose in self.cat_sprites.items():
                # we only need to convert if it's using the old sprite pose numbers
                if not isinstance(pose, int):
                    continue
                poses, i = self._conversion_fetch_poses(age, fur_length)
                if age == CatAge.NEWBORN and pose == "newborn0":
                    poses = ["newborn2"] if "newborn2" in poses else poses
                elif age == CatAge.KITTEN:
                    if i > 0:
                        temp = f"kitten{pose if pose in (0, 1, 2) else 0}"
                        poses = temp if temp in poses else poses
                    else:
                        temp = f"kitten_{fur_length}_{pose if pose in (0, 1, 2) else 0}"
                        poses = temp if temp in poses else poses
                elif age == CatAge.ADOLESCENT:
                    if i > 0:
                        if pose == 3:
                            poses = (
                                [f"adolescent_{fur_length}0"]
                                if f"adolescent0" in poses
                                else poses
                            )
                        elif pose == 4:
                            poses = (
                                [f"adolescent_{fur_length}1"]
                                if f"adolescent_1" in poses
                                else poses
                            )
                        elif pose == 5:
                            poses = (
                                [f"adolescent_{fur_length}2"]
                                if f"adolescent_2" in poses
                                else poses
                            )
                    else:
                        if pose == 3:
                            poses = ["adolescent0"] if "adolescent0" in poses else poses
                        elif pose == 4:
                            poses = ["adolescent1"] if "adolescent1" in poses else poses
                        elif pose == 5:
                            poses = ["adolescent2"] if "adolescent2" in poses else poses
                elif age in (CatAge.YOUNG_ADULT, CatAge.ADULT, CatAge.SENIOR_ADULT):
                    if pose in (0, 9):
                        poses = ["adult_short0"] if "adult0" in poses else poses
                    elif pose in (1, 10):
                        poses = ["adult_short1"] if "adult1" in poses else poses
                    elif pose in (2, 11):
                        poses = ["adult_short2"] if "adult2" in poses else poses
                    elif pose == 6:
                        poses = ["adult_long0"] if "adult3" in poses else poses
                    elif pose == 7:
                        poses = ["adult_long1"] if "adult4" in poses else poses
                    elif pose == 8:
                        poses = ["adult_long2"] if "adult" in poses else poses
                elif age == CatAge.SENIOR and i > 0:
                    if pose in (3, 12):
                        poses = ["senior0"] if "senior0" in poses else poses
                    elif pose in (4, 13):
                        poses = ["senior1"] if "senior1" in poses else poses
                    elif pose in (5, 14):
                        poses = ["senior2"] if "senior2" in poses else poses

                self.cat_sprites[age] = random.choice(poses)

        # now for the updating handling of pose name strings
        else:
            if not adult_sprite:
                adult_sprite = random.choice(
                    self._conversion_compare_poses(None, "adult", fur_length)
                )

            self.cat_sprites = {
                "newborn": self._conversion_compare_poses(
                    newborn_sprite, "newborn", fur_length
                ),
                "kitten": self._conversion_compare_poses(
                    kitten_sprite, "kitten", fur_length
                ),
                "adolescent": self._conversion_compare_poses(
                    adol_sprite, "adolescent", fur_length
                ),
                "young adult": self._conversion_compare_poses(
                    adult_sprite, "young adult", fur_length
                ),
                "adult": self._conversion_compare_poses(
                    adult_sprite, "adult", fur_length
                ),
                "senior adult": self._conversion_compare_poses(
                    adult_sprite, "senior adult", fur_length
                ),
                "senior": self._conversion_compare_poses(
                    senior_sprite, "senior", fur_length
                ),
                "para_adult": self._conversion_compare_poses(
                    para_adult_sprite, "para_adult", fur_length
                ),
                "para_adolescent": self._conversion_compare_poses(
                    None, "para_adolescent", fur_length
                ),
                "para_kitten": self._conversion_compare_poses(
                    None, "para_kitten", fur_length
                ),
            }

    def _conversion_compare_poses(self, pose, age, fur_length) -> str:
        poses = self._conversion_fetch_poses(age, fur_length)[0]
        if pose is not None and pose in poses:
            return pose
        else:
            return random.choice(poses)

    def _conversion_fetch_poses(self, age, fur_length) -> list:
        i = 0
        poses = None
        while not poses:
            if not i:
                poses = getattr(Pelt, f"{age}_{fur_length}_poses_{self.index}", None)
            elif i == 1:
                poses = getattr(Pelt, f"{age}_poses_{self.index}", None)
            elif i == 2:
                for group in getattr(Pelt, f"default_pose_groups_{self.index}"):
                    if age in getattr(Pelt, f"default_pose_groups_{self.index}")[group]:
                        poses = getattr(
                            Pelt, f"{group}_{fur_length}_poses_{self.index}", None
                        )
                        if not poses:
                            poses = getattr(Pelt, f"{group}_poses_{self.index}", None)
            else:
                self._conversion_exception(age)
            i += 1
        return poses, i

    def _conversion_exception(self, age) -> None:
        raise Exception(
            f"Attempted to convert pose for age {age}, but couldn't find a matching pose group or fallback."
        )

    def _init_data(self):
        for f in constants.SPRITE_FOLDERS:
            POSE_DATA = getattr(sprites, f"POSE_DATA_{f}")
            PELT_DATA = getattr(sprites, f"GENERATION_GROUP_DATA_{f}")

            # POSES
            setattr(Pelt, f"all_poses_{f}", POSE_DATA["poses"])
            setattr(Pelt, f"default_pose_groups_{f}", POSE_DATA["fallback"])
            all_poses = POSE_DATA["poses"]
            pose_categories = []
            for pose in all_poses:
                replace = "".join([x for x in pose if x.isdigit()])
                x = pose.replace(replace, "")
                if x not in pose_categories:
                    pose_categories.append(x)
                    setattr(Pelt, f"{x}_poses_{f}", [pose])
                else:
                    getattr(Pelt, f"{x}_poses_{f}").append(pose)

            # PELT COLOURS
            setattr(Pelt, f"all_pelt_colours_{f}", [])
            setattr(Pelt, f"ginger_colours_{f}", [])
            setattr(Pelt, f"black_colours_{f}", [])
            setattr(Pelt, f"white_colours_{f}", [])
            setattr(Pelt, f"brown_colours_{f}", [])

            # COLOUR CATEGORIES
            setattr(
                Pelt,
                f"colour_categories_{f}",
                [
                    getattr(Pelt, f"ginger_colours_{f}"),
                    getattr(Pelt, f"black_colours_{f}"),
                    getattr(Pelt, f"white_colours_{f}"),
                    getattr(Pelt, f"brown_colours_{f}"),
                ],
            )

            for color in PELT_DATA["pelts"]["colors"]:
                getattr(Pelt, f"all_pelt_colours_{f}").extend(color)
                if PELT_DATA["pelts"]["colors"][color] == "white":
                    getattr(Pelt, f"white_colours_{f}").append(color)
                elif PELT_DATA["pelts"]["colors"][color] == "black":
                    getattr(Pelt, f"black_colours_{f}").append(color)
                elif PELT_DATA["pelts"]["colors"][color] == "ginger":
                    getattr(Pelt, f"ginger_colours_{f}").append(color)
                elif PELT_DATA["pelts"]["colors"][color] == "brown":
                    getattr(Pelt, f"brown_colours_{f}").append(color)

            # PELT PATTERNS
            setattr(Pelt, f"pelt_patterns_{f}", [])
            setattr(Pelt, f"tabbies_{f}", [])
            setattr(Pelt, f"spotted_{f}", [])
            setattr(Pelt, f"plain_{f}", [])
            setattr(Pelt, f"exotic_{f}", [])
            setattr(Pelt, f"torties_{f}", [])

            # PATTERN CATEGORIES
            setattr(
                Pelt,
                f"pelt_categories_{f}",
                [
                    getattr(Pelt, f"tabbies_{f}"),
                    getattr(Pelt, f"spotted_{f}"),
                    getattr(Pelt, f"plain_{f}"),
                    getattr(Pelt, f"exotic_{f}"),
                    getattr(Pelt, f"torties_{f}"),
                ],
            )

            for pelt in PELT_DATA["pelts"]["pattern_types"]:
                getattr(Pelt, f"pelt_patterns_{f}").extend(pelt)
                if PELT_DATA["pelts"]["pattern_types"][pelt] == "tabbies":
                    getattr(Pelt, f"tabbies_{f}").append(pelt)
                elif PELT_DATA["pelts"]["pattern_types"][pelt] == "spotted":
                    getattr(Pelt, f"spotted_{f}").append(pelt)
                elif PELT_DATA["pelts"]["pattern_types"][pelt] == "plain":
                    getattr(Pelt, f"plain_{f}").append(pelt)
                elif PELT_DATA["pelts"]["pattern_types"][pelt] == "exotic":
                    getattr(Pelt, f"exotic_{f}").append(pelt)
                elif PELT_DATA["pelts"]["pattern_types"][pelt] == "torties":
                    getattr(Pelt, f"torties_{f}").append(pelt)

            # PELT SPRITE NAMES
            # pelt name used in save files: pelt's spritesheet
            # setattr(Pelt, f"pattern_sprite_names_{f}", {})
            # for sheet, names in PELT_DATA["spritesheet"].items():
            #     for name in names:
            #         getattr(Pelt, f"pattern_sprite_names_{f}").update({name: sheet})
            # getattr(Pelt, f"pattern_sprite_names_{f}").update(
            #     {
            #         "Tortie": None,
            #         "Calico": None,
            #     }
            # )

            # TORTIE PATCHES
            setattr(
                Pelt,
                f"tortie_patches_{f}",
                list(getattr(sprites, f"TORTIE_PATCH_COMBOS_{f}").keys()),
            )
            for sprite_list in getattr(sprites, f"TORTIE_DATA_{f}")["sprite_list"]:
                getattr(Pelt, f"tortie_patches_{f}").extend(sprite_list)

            # WHITE MARKINGS
            for i in ("little", "mid", "high", "mostly", "vitiligo", "points"):
                if i in ("vitiligo", "points"):
                    setattr(Pelt, f"{i}_markings_{f}", [])
                    for sprite_list in getattr(sprites, f"WHITE_{i.upper()}_DATA_{f}")[
                        "sprite_list"
                    ]:
                        getattr(Pelt, f"{i}_markings_{f}").extend(sprite_list)
                else:
                    setattr(
                        Pelt,
                        f"{i}_white_{f}",
                        list(
                            getattr(sprites, f"WHITE_PATCH_COMBOS_{f}")
                            .get(i, {})
                            .keys()
                        ),
                    )
                    for sprite_list in getattr(sprites, f"WHITE_{i.upper()}_DATA_{f}")[
                        "sprite_list"
                    ]:
                        if i == "mostly":
                            getattr(Pelt, f"{i}_white_{f}").extend(
                                [x for x in sprite_list if x != "FULLWHITE"]
                            )
                        else:
                            getattr(Pelt, f"{i}_white_{f}").extend(sprite_list)

            # EYES
            setattr(Pelt, f"all_eye_colours_{f}", [])
            setattr(Pelt, f"yellow_eyes_{f}", [])
            setattr(Pelt, f"green_eyes_{f}", [])
            setattr(Pelt, f"blue_eyes_{f}", [])
            for sprite_list in getattr(sprites, f"EYE_DATA_{f}")["sprite_list"]:
                getattr(Pelt, f"all_eye_colours_{f}").extend(sprite_list.keys())
                for colour in sprite_list:
                    if sprite_list[colour] == "yellow":
                        getattr(Pelt, f"yellow_eyes_{f}").append(colour)
                    elif sprite_list[colour] == "green":
                        getattr(Pelt, f"green_eyes_{f}").append(colour)
                    elif sprite_list[colour] == "blue":
                        getattr(Pelt, f"blue_eyes_{f}").append(colour)

            # SKIN
            setattr(Pelt, f"skin_sprites_{f}", [])
            for sprite_list in getattr(sprites, f"SKIN_DATA_{f}")["sprite_list"]:
                getattr(Pelt, f"skin_sprites_{f}").extend(sprite_list)

        # PELT LENGTH
        setattr(Pelt, "pelt_length", ["short", "medium", "long"])

    @property
    def accessory(self):
        return self._accessory

    @accessory.setter
    def accessory(self, val):
        self.rebuild_sprite = True
        self._accessory = val

    @property
    def scars(self):
        return self._scars

    @scars.setter
    def scars(self, val):
        self.rebuild_sprite = True
        self._scars = val

    @property
    def paralyzed(self):
        return self._paralyzed

    @paralyzed.setter
    def paralyzed(self, val):
        self.rebuild_sprite = True
        self._paralyzed = val

    @property
    def index(self):
        return self._sps_index

    @index.setter
    def index(self, val):
        self.rebuild_sprite = True
        self._sps_index = val

    @staticmethod
    def generate_new_pelt(
        gender: str, species: str, parents: tuple = (), age: str = "adult"
    ):
        new_pelt = Pelt(
            sps_index=(list(constants.SPECIES["species"]).index(species)) + 1
        )

        pelt_white = new_pelt.init_pattern_color(parents, gender)
        new_pelt.init_white_patches(pelt_white, parents)
        new_pelt.init_sprite()
        new_pelt.init_scars(age)
        new_pelt.init_accessories(age)
        new_pelt.init_eyes(parents)
        new_pelt.init_pattern()
        new_pelt.init_tint()

        return new_pelt

    def check_and_convert(self, convert_dict):
        """Checks for old-type properties for the appearance-related properties
        that are stored in Pelt, and converts them. To be run when loading a cat in."""

        # First, convert from some old names that may be in white_patches.
        if self.white_patches == "POINTMARK":
            self.white_patches = "SEALPOINT"
        elif self.white_patches == "PANTS2":
            self.white_patches = "PANTSTWO"
        elif self.white_patches == "ANY2":
            self.white_patches = "ANYTWO"
        elif self.white_patches == "VITILIGO2":
            self.white_patches = "VITILIGOTWO"

        if self.vitiligo == "VITILIGO2":
            self.vitiligo = "VITILIGOTWO"

        # Move white_patches that should be in vit or points.
        if self.white_patches in getattr(Pelt, f"vitiligo_markings_{self.index}"):
            self.vitiligo = self.white_patches
            self.white_patches = None
        elif self.white_patches in getattr(Pelt, f"points_markings_{self.index}"):
            self.points = self.white_patches
            self.white_patches = None

        if self.tortie_pattern and "tortie" in self.tortie_pattern:
            self.tortie_pattern = sub("tortie", "", self.tortie_pattern.lower())
            if self.tortie_pattern == "solid":
                self.tortie_pattern = "single"

        if self.white_patches in convert_dict["old_creamy_patches"]:
            self.white_patches = convert_dict["old_creamy_patches"][self.white_patches]
            self.white_patches_tint = "darkcream"
        elif self.white_patches in ("SEPIAPOINT", "MINKPOINT", "SEALPOINT"):
            self.white_patches_tint = "none"

        # Eye Color Convert Stuff
        if self.eye_colour == "BLUE2":
            self.eye_colour = "COBALT"
        if self.eye_colour2 == "BLUE2":
            self.eye_colour2 = "COBALT"

        if self.eye_colour in ("BLUEYELLOW", "BLUEGREEN"):
            if self.eye_colour == "BLUEYELLOW":
                self.eye_colour2 = "YELLOW"
            elif self.eye_colour == "BLUEGREEN":
                self.eye_colour2 = "GREEN"
            self.eye_colour = "BLUE"

        if self.tortie_marking in convert_dict["old_tortie_patches"]:
            old_pattern = self.tortie_marking
            self.tortie_marking = convert_dict["old_tortie_patches"][old_pattern][1]

            # If the pattern is old, there is also a chance the base color is stored in
            # tortie_colour. That may be different from the pelt color ("main" for torties)
            # generated before the "ginger-on-ginger" update. If it was generated after that update,
            # tortie_colour and pelt_colour will be the same. Therefore, let's also re-set the pelt color
            self.colour = self.tortie_colour
            self.tortie_colour = convert_dict["old_tortie_patches"][old_pattern][0]

        if self.tortie_marking == "MINIMAL1":
            self.tortie_marking = "MINIMALONE"
        elif self.tortie_marking == "MINIMAL2":
            self.tortie_marking = "MINIMALTWO"
        elif self.tortie_marking == "MINIMAL3":
            self.tortie_marking = "MINIMALTHREE"
        elif self.tortie_marking == "MINIMAL4":
            self.tortie_marking = "MINIMALFOUR"

        if self.accessory is None:
            self.accessory = tuple()
        elif isinstance(self.accessory, str):
            self.accessory = tuple([self.accessory])

        new_acc_list = []
        for acc in self.accessory:
            if acc in convert_dict["collar_map"]:
                new_acc_list.append(convert_dict["collar_map"][acc])
            else:
                new_acc_list.append(acc)
        self.accessory = tuple(new_acc_list)

    def init_eyes(self, parents):
        """Sets eye color for this cat's pelt. Takes parents' eye colors into account.
        Heterochromia is possible based on the white-ness of the pelt, so the pelt color and white_patches must be
        set before this function is called.

        :param parents: List[Cat] representing this cat's parents

        :return: None
        """
        if not parents:
            self.eye_colour = random.choice(
                getattr(Pelt, f"all_eye_colours_{self.index}")
            )
        else:
            self.eye_colour = random.choice(
                [i.pelt.eye_colour for i in parents if i.pelt.index == self.index]
                + [random.choice(getattr(Pelt, f"all_eye_colours_{self.index}"))]
            )

        # White patches must be initialized before eye color.
        num = constants.CONFIG["cat_generation"]["base_heterochromia"]
        if (
            self.white_patches in getattr(Pelt, f"high_white_{self.index}")
            or self.white_patches in getattr(Pelt, f"mostly_white_{self.index}")
            or self.white_patches == "FULLWHITE"
            or self.colour == "WHITE"
        ):
            num = num - 90
        if self.white_patches == "FULLWHITE" or self.colour == "WHITE":
            num -= 10
        for _par in parents:
            if _par.pelt.eye_colour2:
                num -= 10

        if num < 0:
            num = 1

        if not random.randint(0, num):
            colour_wheel = [
                getattr(Pelt, f"yellow_eyes_{self.index}"),
                getattr(Pelt, f"blue_eyes_{self.index}"),
                getattr(Pelt, f"green_eyes_{self.index}"),
            ]
            for colour in colour_wheel[:]:
                if self.eye_colour in colour:
                    colour_wheel.remove(
                        colour
                    )  # removes the selected list from the options
                    self.eye_colour2 = random.choice(
                        random.choice(colour_wheel)
                    )  # choose from the remaining two lists
                    break

    def pattern_color_inheritance(self, parents: tuple = (), gender="female"):
        # setting parent pelt categories
        # We are using a set, since we don't need this to be ordered, and sets deal with removing duplicates.
        par_peltlength = set()
        par_peltcolours = []
        par_peltnames = []
        par_index = []
        par_pelts = []
        par_white = []
        for p in parents:
            if p:
                # Gather pelt length
                par_peltlength.add(p.pelt.length)

                # Gather pelt color.
                par_peltcolours.append(p.pelt.colour)

                # Gather pelt name
                if p.pelt.name in getattr(Pelt, f"torties_{p.pelt.index}"):
                    par_peltnames.append(p.pelt.tortie_base.capitalize())
                else:
                    par_peltnames.append(p.pelt.name)

                # Gatcher species index.
                par_index.append(p.pelt.index)

                # Gather exact pelts, if same species as kit, for direct inheritance.
                if p.pelt.index == self.index:
                    par_pelts.append(p.pelt)

                # Gather if they have white in their pelt.
                par_white.append(p.pelt.white)
            else:
                # If order for white patches to work correctly, we also want to randomly generate a "pelt_white"
                # for each "None" parent (missing or unknown parent)
                par_white.append(bool(random.getrandbits(1)))

                # Append None
                # Gather pelt color.
                par_peltcolours.append(None)
                par_peltlength.add(None)
                par_peltnames.append(None)

        # If this list is empty, something went wrong.
        if not par_peltcolours:
            print("Warning - no parents: pelt randomized")
            return self.randomize_pattern_color(gender)

        # There is a 1/10 chance for kits to have the exact same pelt as one of their parents
        if (
            not random.randint(
                0, constants.CONFIG["cat_generation"]["direct_inheritance"]
            )
            and par_pelts
        ):  # 1/10 chance
            selected = random.choice(par_pelts)
            self.name = selected.name
            self.length = selected.length
            self.colour = selected.colour
            self.tortie_base = selected.tortie_base
            return selected.white

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT
        # ------------------------------------------------------------------------------------------------------------#

        # Determine pelt.
        weights = [
            0,
            0,
            0,
            0,
        ]  # Weights for each pelt group. It goes: (tabbies, spotted, plain, exotic)
        for i, p_ in enumerate(par_peltnames):
            if p_ in getattr(Pelt, f"tabbies_{par_index[i]}"):
                add_weight = (50, 10, 5, 7)
            elif p_ in getattr(Pelt, f"spotted_{par_index[i]}"):
                add_weight = (10, 50, 5, 5)
            elif p_ in getattr(Pelt, f"plain_{par_index[i]}"):
                add_weight = (5, 5, 50, 0)
            elif p_ in getattr(Pelt, f"exotic_{par_index[i]}"):
                add_weight = (15, 15, 1, 45)
            elif (
                p_ is None
            ):  # If there is at least one unknown parent, a None will be added to the set.
                add_weight = (35, 20, 30, 15)
            else:
                add_weight = (0, 0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weight[x]

        # A quick check to make sure all the weights aren't 0
        if all([x == 0 for x in weights]):
            weights = [1, 1, 1, 1]

        # Now, choose the pelt category and pelt
        possible_pelts = getattr(Pelt, f"pelt_categories_{self.index}").copy()
        possible_pelts.pop(-1)  # remove torties
        chosen_pelt = random.choice(
            random.choices(possible_pelts, weights=weights, k=1)[0]
        )

        # Tortie chance
        tortie_chance_f = constants.CONFIG["cat_generation"][
            "base_female_tortie"
        ]  # There is a default chance for female tortie
        tortie_chance_m = constants.CONFIG["cat_generation"]["base_male_tortie"]
        for p_ in par_pelts:
            if p_.name in getattr(Pelt, f"torties_{p_.index}"):
                tortie_chance_f = int(tortie_chance_f / 2)
                tortie_chance_m = tortie_chance_m - 1
                break

        # Determine tortie:
        if gender == "female":
            torbie = random.getrandbits(tortie_chance_f) == 1
        else:
            torbie = random.getrandbits(tortie_chance_m) == 1

        chosen_tortie_base = None
        if torbie:
            # If it is tortie, the chosen pelt above becomes the base pelt.
            chosen_tortie_base = chosen_pelt
            # if chosen_tortie_base in ("TwoColour", "SingleColour"):
            #    chosen_tortie_base = "Single"
            chosen_tortie_base = chosen_tortie_base
            chosen_pelt = random.choice(getattr(Pelt, f"torties_{self.index}"))

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT COLOUR
        # ------------------------------------------------------------------------------------------------------------#
        # Weights for each colour group. It goes: (ginger_colours, black_colours, white_colours, brown_colours)
        weights = [0, 0, 0, 0]
        for i, p_ in enumerate(par_peltcolours):
            if p_ in getattr(Pelt, f"ginger_colours_{par_index[i]}"):
                add_weight = (40, 0, 0, 10)
            elif p_ in getattr(Pelt, f"black_colours_{par_index[i]}"):
                add_weight = (0, 40, 2, 5)
            elif p_ in getattr(Pelt, f"white_colours_{par_index[i]}"):
                add_weight = (0, 5, 40, 0)
            elif p_ in getattr(Pelt, f"brown_colours_{par_index[i]}"):
                add_weight = (10, 5, 0, 35)
            elif p_ is None:
                add_weight = (40, 40, 40, 40)
            else:
                add_weight = (0, 0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weight[x]

            # A quick check to make sure all the weights aren't 0
            if all([x == 0 for x in weights]):
                weights = [1, 1, 1, 1]

        chosen_pelt_color = random.choice(
            random.choices(
                getattr(Pelt, f"colour_categories_{self.index}"), weights=weights, k=1
            )[0]
        )

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT LENGTH
        # ------------------------------------------------------------------------------------------------------------#

        weights = [0, 0, 0]  # Weights for each length. It goes (short, medium, long)
        for p_ in par_peltlength:
            if p_ == "short":
                add_weight = (50, 10, 2)
            elif p_ == "medium":
                add_weight = (25, 50, 25)
            elif p_ == "long":
                add_weight = (2, 10, 50)
            elif p_ is None:
                add_weight = (10, 10, 10)
            else:
                add_weight = (0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weight[x]

        # A quick check to make sure all the weights aren't 0
        if all([x == 0 for x in weights]):
            weights = [1, 1, 1]

        chosen_pelt_length = random.choices(
            getattr(Pelt, "pelt_length"), weights=weights, k=1
        )[0]

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT WHITE
        # ------------------------------------------------------------------------------------------------------------#

        # There are 94 percentage points that can be added by
        # parents having white. If we have more than two, this
        # will keep that the same.
        percentage_add_per_parent = int(94 / len(par_white))
        chance = 3
        for p_ in par_white:
            if p_:
                chance += percentage_add_per_parent

        chosen_white = random.randint(1, 100) <= chance

        # Adjustments to pelt chosen based on if the pelt has white in it or not.
        if chosen_pelt in ("TwoColour", "SingleColour"):
            if chosen_white:
                chosen_pelt = "TwoColour"
            else:
                chosen_pelt = "SingleColour"
        elif chosen_pelt == "Calico":
            if not chosen_white:
                chosen_pelt = "Tortie"

        # SET THE PELT
        self.name = chosen_pelt
        self.colour = chosen_pelt_color
        self.length = chosen_pelt_length
        self.tortie_base = (
            chosen_tortie_base  # This will be none if the cat isn't a tortie.
        )
        return chosen_white

    def randomize_pattern_color(self, gender):
        # ------------------------------------------------------------------------------------------------------------#
        #   PELT
        # ------------------------------------------------------------------------------------------------------------#
        # Determine pelt.
        possible_pelts = getattr(Pelt, f"pelt_categories_{self.index}").copy()
        possible_pelts.pop(-1)  # remove torties
        chosen_pelt = random.choice(
            random.choices(possible_pelts, weights=(35, 20, 30, 15), k=1)[0]
        )

        # Tortie chance
        # There is a default chance for female tortie, slightly increased for completely random generation.
        tortie_chance_f = constants.CONFIG["cat_generation"]["base_female_tortie"] - 1
        tortie_chance_m = constants.CONFIG["cat_generation"]["base_male_tortie"]
        if gender == "female":
            torbie = random.getrandbits(tortie_chance_f) == 1
        else:
            torbie = random.getrandbits(tortie_chance_m) == 1

        chosen_tortie_base = None
        if torbie:
            # If it is tortie, the chosen pelt above becomes the base pelt.
            chosen_tortie_base = chosen_pelt
            # if chosen_tortie_base in ("TwoColour", "SingleColour"):
            #    chosen_tortie_base = "Single"
            chosen_tortie_base = chosen_tortie_base
            chosen_pelt = random.choice(getattr(Pelt, f"torties_{self.index}"))

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT COLOUR
        # ------------------------------------------------------------------------------------------------------------#

        chosen_pelt_color = random.choice(
            random.choices(getattr(Pelt, f"colour_categories_{self.index}"), k=1)[0]
        )

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT LENGTH
        # ------------------------------------------------------------------------------------------------------------#

        chosen_pelt_length = random.choice(getattr(Pelt, "pelt_length"))

        # ------------------------------------------------------------------------------------------------------------#
        #   PELT WHITE
        # ------------------------------------------------------------------------------------------------------------#

        chosen_white = random.randint(1, 100) <= 40

        # Adjustments to pelt chosen based on if the pelt has white in it or not.
        if chosen_pelt in ("TwoColour", "SingleColour"):
            if chosen_white:
                chosen_pelt = "TwoColour"
            else:
                chosen_pelt = "SingleColour"
        elif chosen_pelt == "Calico":
            if not chosen_white:
                chosen_pelt = "Tortie"

        self.name = chosen_pelt
        self.colour = chosen_pelt_color
        self.length = chosen_pelt_length
        self.tortie_base = (
            chosen_tortie_base  # This will be none if the cat isn't a tortie.
        )
        return chosen_white

    def init_pattern_color(self, parents, gender) -> bool:
        """Initializes self.name, self.colour, self.length,
        self.tortie_base and determines if the cat
        will have white patche or not.
        Return TRUE is the cat should have white patches,
        false is not."""

        if parents:
            # If the cat has parents, use inheritance to decide pelt.
            chosen_white = self.pattern_color_inheritance(parents, gender)
        else:
            chosen_white = self.randomize_pattern_color(gender)

        return chosen_white

    def init_sprite(self):
        # skin chances
        self.skin = random.choice(getattr(Pelt, f"skin_sprites_{self.index}"))

        fur_length = self.length if self.length != "medium" else "short"
        self.cat_sprites = {
            "newborn": random.choice(
                self._conversion_fetch_poses("newborn", fur_length)[0]
            ),
            "kitten": random.choice(
                self._conversion_fetch_poses("kitten", fur_length)[0]
            ),
            "adolescent": random.choice(
                self._conversion_fetch_poses("adolescent", fur_length)[0]
            ),
            "adult": random.choice(
                self._conversion_fetch_poses("adult", fur_length)[0]
            ),
            "senior": random.choice(
                self._conversion_fetch_poses("senior", fur_length)[0]
            ),
            "para_adult": random.choice(
                self._conversion_fetch_poses("para_adult", fur_length)[0]
            ),
            "para_adolescent": random.choice(
                self._conversion_fetch_poses("para_adolescent", fur_length)[0]
            ),
            "para_kitten": random.choice(
                self._conversion_fetch_poses("para_kitten", fur_length)[0]
            )
        }
        self.cat_sprites["young adult"] = self.cat_sprites["adult"]
        self.cat_sprites["senior adult"] = self.cat_sprites["adult"]
        self.reverse = bool(random.getrandbits(1))

    def init_scars(self, age):
        if age == "newborn":
            return

        if age in ("kitten", "adolescent"):
            scar_choice = random.randint(0, 50)  # 2%
        elif age in ("young adult", "adult"):
            scar_choice = random.randint(0, 20)  # 5%
        else:
            scar_choice = random.randint(0, 15)  # 6.67%

        if scar_choice == 1:
            self.scars = (*self.scars, random.choice(getattr(Pelt, "general_scars")))

        if "NOTAIL" in self.scars and "HALFTAIL" in self.scars:
            self.scars = tuple(scar for scar in self.scars if scar != "HALFTAIL")

    def init_accessories(self, age):
        if age == "newborn":
            self.accessory = tuple()
            return

        acc_display_choice = random.randint(0, 80)
        if age in ("kitten", "adolescent"):
            acc_display_choice = random.randint(0, 180)
        elif age in ("young adult", "adult"):
            acc_display_choice = random.randint(0, 100)

        if acc_display_choice == 1:
            self.accessory = tuple(
                (
                    random.choice(
                        getattr(Pelt, "plant_accessories")
                        + getattr(Pelt, "wild_accessories")
                    )
                )
            )
        else:
            self.accessory = tuple()

    def init_pattern(self):
        if self.name in getattr(Pelt, f"torties_{self.index}"):
            if not self.tortie_base:
                self.tortie_base = random.choice(
                    getattr(Pelt, f"pelt_patterns_{self.index}")
                )
            if not self.tortie_marking:
                self.tortie_marking = random.choice(
                    getattr(Pelt, f"tortie_patches_{self.index}")
                )

            wildcard_chance = constants.CONFIG["cat_generation"]["wildcard_tortie"]
            if self.colour:
                # The "not wildcard_chance" allows users to set wildcard_tortie to 0
                # and always get wildcard torties.
                if not wildcard_chance or random.getrandbits(wildcard_chance) == 1:
                    # This is the "wildcard" chance, where you can get funky combinations.
                    # people are fans of the print message, so I'm putting it back
                    print("Wildcard tortie!")

                    # Allow any pattern, minus torties:
                    self.tortie_pattern = random.choice(
                        getattr(Pelt, f"tabbies_{self.index}")
                        + getattr(Pelt, f"spotted_{self.index}")
                        + getattr(Pelt, f"plain_{self.index}")
                        + getattr(Pelt, f"exotic_{self.index}")
                    )

                    # Allow any colors that aren't the base color.
                    possible_colors = getattr(
                        Pelt, f"all_pelt_colours_{self.index}"
                    ).copy()
                    possible_colors.remove(self.colour)
                    self.tortie_colour = random.choice(possible_colors)

                else:
                    # Normal generation
                    if self.tortie_base in ("SingleStripe", "Smoke"):
                        self.tortie_pattern = random.choice(
                            [
                                "Tabby",
                                "Mackerel",
                                "Classic",
                                "SingleColour",
                                "Smoke",
                                "Agouti",
                                "Ticked",
                            ]
                        )
                    else:
                        self.tortie_pattern = random.choices(
                            [self.tortie_base, "SingleColour"], weights=[97, 3], k=1
                        )[0]

                    white_colours = getattr(Pelt, f"white_colours_{self.index}")
                    black_colours = getattr(Pelt, f"black_colours_{self.index}")
                    ginger_colours = getattr(Pelt, f"ginger_colours_{self.index}")
                    brown_colours = getattr(Pelt, f"brown_colours_{self.index}")

                    if self.colour == "WHITE":
                        possible_colors = white_colours.copy()
                        possible_colors.remove("WHITE")
                        self.colour = random.choice(possible_colors)

                    # Ginger is often duplicated to increase its chances
                    if (self.colour in black_colours) or (self.colour in white_colours):
                        self.tortie_colour = random.choice(
                            (ginger_colours * 2) + brown_colours
                        )
                    elif self.colour in ginger_colours:
                        self.tortie_colour = random.choice(
                            brown_colours + black_colours * 2
                        )
                    elif self.colour in brown_colours:
                        possible_colors = brown_colours.copy()
                        possible_colors.remove(self.colour)
                        possible_colors.extend(black_colours + (ginger_colours * 2))
                        self.tortie_colour = random.choice(possible_colors)
                    else:
                        self.tortie_colour = "GOLDEN"

            else:
                self.tortie_colour = "GOLDEN"
        else:
            self.tortie_base = None
            self.tortie_pattern = None
            self.tortie_colour = None
            self.tortie_marking = None

    def white_patches_inheritance(self, parents: tuple):
        par_whitepatches = []
        par_points = []
        par_index = []
        for p in parents:
            if p:
                if p.pelt.white_patches:
                    par_whitepatches.append(p.pelt.white_patches)
                else:
                    par_whitepatches.append(None)
                if p.pelt.points:
                    par_points.append(p.pelt.points)
                par_index.append(p.pelt.index)

        if not parents:
            print("Error - no parents. Randomizing white patches.")
            self.randomize_white_patches()
            return

        # Direct inheritance. Will only work if at least one parent has white patches, otherwise continue on.
        if par_whitepatches and not random.randint(
            0, constants.CONFIG["cat_generation"]["direct_inheritance"]
        ):
            # This ensures Torties and Calicos won't get direct inheritance of incorrect white patch types
            _temp = par_whitepatches.copy()
            if self.name == "Tortie":
                for i, p in enumerate(_temp.copy()):
                    if (
                        p
                        in (
                            getattr(Pelt, f"high_white_{self.index}")
                            + getattr(Pelt, f"mostly_white_{self.index}")
                            + ["FULLWHITE"]
                        )
                        or par_index[i] != self.index
                        or not p
                    ):
                        _temp.remove(p)
            elif self.name == "Calico":
                for i, p in enumerate(_temp.copy()):
                    if (
                        p
                        in (
                            getattr(Pelt, f"little_white_{self.index}")
                            + getattr(Pelt, f"mid_white_{self.index}")
                        )
                        or par_index[i] != self.index
                        or not p
                    ):
                        _temp.remove(p)

            # Only proceed with the direct inheritance if there are white patches that match the pelt.
            if _temp:
                self.white_patches = random.choice(list(_temp))

                # Direct inheritance also effect the point marking.
                self.points = None
                if par_points and self.name != "Tortie":
                    selected_points = random.choice(par_points)
                    if selected_points in getattr(
                        Pelt, f"points_markings_{self.index}"
                    ):
                        self.points = selected_points

                return

        # dealing with points
        if par_points:
            chance = 10 - len(par_points)
        else:
            chance = 40
        # Chance of point is 1 / chance.
        if self.name != "Tortie" and not int(random.random() * chance):
            self.points = random.choice(getattr(Pelt, f"points_markings_{self.index}"))
        else:
            self.points = None

        white_list = [
            getattr(Pelt, f"little_white_{self.index}"),
            getattr(Pelt, f"mid_white_{self.index}"),
            getattr(Pelt, f"high_white_{self.index}"),
            getattr(Pelt, f"mostly_white_{self.index}"),
            ["FULLWHITE"],
        ]

        weights = [0, 0, 0, 0, 0]  # Same order as white_list
        for i, p_ in enumerate(par_whitepatches):
            if p_ in getattr(Pelt, f"little_white_{par_index[i]}"):
                add_weights = (40, 20, 15, 5, 0)
            elif p_ in getattr(Pelt, f"mid_white_{par_index[i]}"):
                add_weights = (10, 40, 15, 10, 0)
            elif p_ in getattr(Pelt, f"high_white_{par_index[i]}"):
                add_weights = (15, 20, 40, 10, 1)
            elif getattr(Pelt, f"mostly_white_{par_index[i]}"):
                add_weights = (5, 15, 20, 40, 5)
            elif p_ == "FULLWHITE":
                add_weights = (0, 5, 15, 40, 10)
            else:
                add_weights = (0, 0, 0, 0, 0)

            for x in range(0, len(weights)):
                weights[x] += add_weights[x]

        # If all the weights are still 0, that means none of the parents have white patches.
        if not any(weights):
            if not all(
                parents
            ):  # If any of the parents are None (unknown), use the following distribution:
                weights = [20, 10, 10, 5, 0]
            else:
                # Otherwise, all parents are known and don't have any white patches. Focus distribution on little_white.
                weights = [50, 5, 0, 0, 0]

        # Adjust weights for torties, since they can't have anything greater than mid_white:
        if self.name == "Tortie":
            weights = weights[:2] + [0, 0, 0]
            # Another check to make sure not all the values are zero. This should never happen, but better
            # safe than sorry.
            if not any(weights):
                weights = [2, 1, 0, 0, 0]
        elif self.name == "Calico":
            weights = [0, 0, 0] + weights[3:]
            # Another check to make sure not all the values are zero. This should never happen, but better
            # safe than sorry.
            if not any(weights):
                weights = [2, 1, 0, 0, 0]

        chosen_white_patches = random.choice(
            random.choices(white_list, weights=weights, k=1)[0]
        )

        self.white_patches = chosen_white_patches
        if self.points and self.white_patches in (
            getattr(Pelt, f"high_white_{self.index}"),
            getattr(Pelt, f"mostly_white_{self.index}"),
            "FULLWHITE",
        ):
            self.points = None

    def randomize_white_patches(self):
        # Points determination. Tortie can't be pointed
        if self.name != "Tortie" and not random.getrandbits(
            constants.CONFIG["cat_generation"]["random_point_chance"]
        ):
            # Cat has colorpoint!
            self.points = random.choice(getattr(Pelt, f"points_markings_{self.index}"))
        else:
            self.points = None

        # Adjust weights for torties, since they can't have anything greater than mid_white:
        if self.name == "Tortie":
            weights = (2, 1, 0, 0, 0)
        elif self.name == "Calico":
            weights = (0, 0, 20, 15, 1)
        else:
            weights = (10, 10, 10, 10, 1)

        white_list = [
            getattr(Pelt, f"little_white_{self.index}"),
            getattr(Pelt, f"mid_white_{self.index}"),
            getattr(Pelt, f"high_white_{self.index}"),
            getattr(Pelt, f"mostly_white_{self.index}"),
            ["FULLWHITE"],
        ]
        chosen_white_patches = random.choice(
            random.choices(white_list, weights=weights, k=1)[0]
        )

        self.white_patches = chosen_white_patches
        if self.points and self.white_patches in (
            getattr(Pelt, f"high_white_{self.index}"),
            getattr(Pelt, f"mostly_white_{self.index}"),
            "FULLWHITE",
        ):
            self.points = None

    def init_white_patches(self, pelt_white, parents: tuple):
        # Vit can roll for anyone, not just cats who rolled to have white in their pelt.
        par_vit = []
        for p in parents:
            if p:
                if p.pelt.vitiligo:
                    par_vit.append(p.pelt.vitiligo)

        vit_chance = max(
            constants.CONFIG["cat_generation"]["vit_chance"] - len(par_vit), 0
        )
        if not random.getrandbits(vit_chance):
            self.vitiligo = random.choice(
                getattr(Pelt, f"vitiligo_markings_{self.index}")
            )

        # If the cat was rolled previously to have white patches, then determine the patch they will have
        # these functions also handle points.
        if pelt_white:
            if parents:
                self.white_patches_inheritance(parents)
            else:
                self.randomize_white_patches()
        else:
            self.white_patches = None
            self.points = None

    def init_tint(self):
        """Sets tint for pelt and white patches"""
        # PELT TINT
        cat_tints = getattr(sprites, f"cat_tints_{self.index}")
        # Basic tints as possible for all colors.
        base_tints = cat_tints["possible_tints"]["basic"]
        if self.colour in cat_tints["colour_groups"]:
            color_group = cat_tints["colour_groups"].get(self.colour, "warm")
            color_tints = cat_tints["possible_tints"][color_group]
        else:
            color_tints = []

        if base_tints or color_tints:
            self.tint = random.choice(base_tints + color_tints)
        else:
            self.tint = None

        # WHITE PATCHES TINT
        white_patches_tints = getattr(sprites, f"white_patches_tints_{self.index}")
        if self.white_patches or self.points:
            # Now for white patches
            base_tints = white_patches_tints["possible_tints"]["basic"]
            if self.colour in cat_tints["colour_groups"]:
                color_group = white_patches_tints["colour_groups"].get(
                    self.colour, "white"
                )
                color_tints = white_patches_tints["possible_tints"][color_group]
            else:
                color_tints = []

            if base_tints or color_tints:
                self.white_patches_tint = random.choice(base_tints + color_tints)
            else:
                self.white_patches_tint = None
        else:
            self.white_patches_tint = None

    @property
    def white(self):
        return self.white_patches or self.points

    @white.setter
    def white(self, val):
        raise Exception(
            f"Attempted to set cat's white patches to {val}, but pelt.white cannot be used to set a white patches"
        )

    def describe_eyes(self):
        return (
            adjust_list_text(
                [
                    i18n.t(f"cat.eyes.{self.eye_colour}"),
                    i18n.t(f"cat.eyes.{self.eye_colour2}"),
                ]
            )
            if self.eye_colour2
            else i18n.t(f"cat.eyes.{self.eye_colour}")
        )

    @staticmethod
    def describe_appearance(cat, short=False):
        """Return a description of a cat

        :param Cat cat: The cat to describe
        :param bool short: Whether to return a heavily-truncated description, default False
        :return str: The cat's description
        """

        config = get_lang_config()["description"]
        ruleset = config["ruleset"]
        output = []
        pelt_pattern, pelt_color = _describe_pattern(cat, short)
        for rule, args in ruleset.items():
            temp = unpack_appearance_ruleset(cat, rule, short, pelt_pattern, pelt_color)

            if args == "" or temp == "":
                output.append(temp)
                continue

            # handle args
            arg_pool = {
                arg: unpack_appearance_ruleset(
                    cat, arg, short, pelt_pattern, pelt_color
                )
                for arg in args
            }
            arg_pool["key"] = temp
            arg_pool["count"] = 1 if short else 2
            output.append(i18n.t(**arg_pool))

        # don't forget the count argument!
        groups = []
        for grouping in config["groups"]:
            temp = ""
            items = [
                i18n.t(output[i], count=1 if short else 2)
                for i in grouping["values"]
                if output[i] != ""
            ]
            if len(items) == 0:
                continue
            if "pre_value" in grouping:
                temp = grouping["pre_value"]

            if grouping["format"] == "list":
                temp += adjust_list_text(items)
            else:
                temp += grouping["format"].join(items)

            if "post_value" in grouping:
                temp += grouping["post_value"]
            groups.append(temp)

        return "".join(groups)

    """
    def get_sprites_name(self):
        return getattr(Pelt, f"pattern_sprite_names_{self.index}")[self.name]
    """


def _describe_pattern(cat, short=False):
    color_name = [f"cat.pelts.{str(cat.pelt.colour)}"]
    pelt_name = f"cat.pelts.{cat.pelt.name}{'' if short else '_long'}"
    if cat.pelt.name in getattr(Pelt, f"torties_{cat.pelt.index}"):
        pelt_name, color_name = _describe_torties(cat, color_name, short)

    color_name = [i18n.t(piece, count=1) for piece in color_name]
    color_name = "".join(color_name)

    if cat.pelt.white_patches:
        if cat.pelt.white_patches == "FULLWHITE":
            # If the cat is fullwhite, discard all other information. They are just white
            color_name = i18n.t("cat.pelts.FULLWHITE")
            pelt_name = f"cat.pelts.SingleColour_long"
        elif cat.pelt.name != "Calico":
            white = i18n.t("cat.pelts.FULLWHITE")
            if i18n.t("cat.pelts.WHITE", count=1) in color_name:
                color_name = white
            elif cat.pelt.white_patches in getattr(
                Pelt, f"mostly_white_{cat.pelt.index}"
            ):
                color_name = adjust_list_text([white, color_name])
            else:
                color_name = adjust_list_text([color_name, white])

    if cat.pelt.points:
        color_name = i18n.t("cat.pelts.point", color=color_name)
        if "ginger point" in color_name:
            color_name.replace("ginger point", "flame point")
            # look, I'm leaving this as a quirk of the english language, if it's a problem elsewhere lmk

    return pelt_name, color_name


def _describe_torties(cat, color_name, short=False) -> (str, str):
    # Calicos and Torties need their own descriptions
    mottled_colours = (
        getattr(Pelt, f"black_colours_{cat.pelt.index}")
        + getattr(Pelt, f"brown_colours_{cat.pelt.index}")
        + getattr(Pelt, f"white_colours_{cat.pelt.index}")
    )
    if short:
        # If using short, don't describe the colors of calicos and torties.
        # Just call them calico, tortie, or mottled
        if (
            cat.pelt.colour in mottled_colours
            and cat.pelt.tortie_colour in mottled_colours
        ):
            return "cat.pelts.mottled", ""
        else:
            return f"cat.pelts.{cat.pelt.name}", ""

    base = cat.pelt.tortie_base.lower()

    patches_color = f"cat.pelts.{cat.pelt.tortie_colour}"
    color_name.append("/")
    color_name.append(patches_color)

    if cat.pelt.colour in mottled_colours and cat.pelt.tortie_colour in mottled_colours:
        return "cat.pelts.mottled_long", color_name
    else:
        if base in tuple(
            tabby.lower() for tabby in getattr(Pelt, f"tabbies_{cat.pelt.index}")
        ) + (
            "bengal",
            "rosette",
            "speckled",
        ):
            base = f"cat.pelts.{cat.pelt.name}_tabby_long"
        else:
            base = f"cat.pelts.{cat.pelt.name}_long"
        return base, color_name


_scar_details = [
    "NOTAIL",
    "HALFTAIL",
    "NOPAW",
    "NOLEFTEAR",
    "NORIGHTEAR",
    "NOEAR",
]


def unpack_appearance_ruleset(cat, rule, short, pelt, color):
    if rule == "scarred":
        if not short and len(cat.pelt.scars) >= 3:
            return "cat.pelts.scarred"
    elif rule == "fur_length":
        if not short and cat.pelt.length == "long":
            return "cat.pelts.long_furred"
    elif rule == "pattern":
        return pelt
    elif rule == "color":
        return color
    elif rule == "cat":
        if cat.genderalign in ("female", "trans female"):
            return "general.she-cat"
        elif cat.genderalign in ("male", "trans male"):
            return "general.tom"
        else:
            return "general.cat"
    elif rule == "vitiligo":
        if not short and cat.pelt.vitiligo:
            return "cat.pelts.vitiligo"
    elif rule == "amputation":
        if not short:
            scarlist = []
            for scar in cat.pelt.scars:
                if scar in _scar_details:
                    scarlist.append(i18n.t(f"cat.pelts.{scar}"))
            return (
                adjust_list_text(list(set(scarlist))) if len(scarlist) > 0 else ""
            )  # note: this doesn't preserve order!
    else:
        raise Exception(f"Unmatched ruleset item {rule} in describe_appearance!")
    return ""

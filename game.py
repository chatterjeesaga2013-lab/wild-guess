"""Rules for Wild Guess. No Streamlit code here, so the game is easy to test."""

import random
import re

# Each feature has one consistent meaning across the whole animal roster.
FEATURES = {
    "mammal": "Is it a mammal?",
    "bird": "Is it a bird?",
    "reptile": "Is it a reptile?",
    "fish": "Is it a fish?",
    "amphibian": "Is it an amphibian?",
    "insect": "Is it an insect?",
    "flies": "Can it fly by itself?",
    "wings": "Does it have wings?",
    "aquatic": "Does it regularly spend much of its life in water?",
    "ocean": "Does it naturally live in the ocean?",
    "eggs": "Does it lay eggs?",
    "predator": "Does it feed mainly on other animals?",
    "plant_eater": "Does it feed mainly on plants?",
    "nocturnal": "Is it mainly active at night?",
    "large": "Is a typical adult heavier than a human?",
    "human_kept": "Is it commonly kept by humans as a pet or working/farm animal?",
    "stripes": "Does it have prominent stripes?",
    "spots": "Does it have prominent spots or coat patches?",
    "shell": "Does it have a hard protective shell?",
    "horn": "Does it have a horn on its nose?",
    "trunk": "Does it have a trunk?",
    "long_neck": "Is it known for a very long neck?",
    "visible_scales": "Does it have visible scaly skin?",
    "hops": "Is it known for hopping or jumping?",
    "polar": "Is it naturally associated with polar climates?",
    "eight_arms": "Does it have eight arms?",
    "feathers": "Does it have feathers?",
    "furry": "Does it have an obvious coat of fur or hair?",
    "pouch": "Does it have a pouch for carrying babies?",
    "color_change": "Is it known for changing its body color?",
    "stinger": "Does it have a stinger?",
    "desert": "Is it particularly adapted to living in deserts?",
}

# Fixed facts make the answer to a question consistent from start to finish.
# Species with highly variable traits are intentionally avoided where possible.
ANIMALS = {
    "tiger": "mammal predator nocturnal large stripes furry",
    "lion": "mammal predator nocturnal large furry",
    "elephant": "mammal plant_eater large trunk",
    "giraffe": "mammal plant_eater large spots long_neck furry",
    "zebra": "mammal plant_eater large stripes furry",
    "giant panda": "mammal plant_eater large furry",
    "kangaroo": "mammal plant_eater hops pouch furry",
    "dolphin": "mammal aquatic ocean predator large",
    "great white shark": "fish aquatic ocean predator large",
    "octopus": "aquatic ocean predator eggs eight_arms color_change",
    "penguin": "bird aquatic ocean predator eggs polar feathers wings",
    "eagle": "bird flies wings eggs predator feathers",
    "owl": "bird flies wings eggs predator nocturnal feathers",
    "parrot": "bird flies wings eggs plant_eater human_kept feathers",
    "bat": "mammal flies wings predator nocturnal furry",
    "crocodile": "reptile aquatic eggs predator large visible_scales",
    "sea turtle": "reptile aquatic ocean eggs shell visible_scales",
    "frog": "amphibian aquatic eggs predator hops",
    "cobra": "reptile eggs predator visible_scales",
    "chameleon": "reptile eggs predator visible_scales color_change",
    "butterfly": "insect flies wings eggs plant_eater",
    "honeybee": "insect flies wings eggs plant_eater stinger",
    "wolf": "mammal predator furry",
    "rabbit": "mammal plant_eater human_kept hops furry",
    "cat": "mammal predator nocturnal human_kept furry",
    "dog": "mammal human_kept furry",
    "polar bear": "mammal predator large polar furry",
    "camel": "mammal plant_eater large human_kept long_neck furry desert",
    "cheetah": "mammal predator large spots furry",
    "rhinoceros": "mammal plant_eater large horn",
}
ANIMALS = {animal: set(features.split()) for animal, features in ANIMALS.items()}
MAX_TURNS = 12

ALIASES = {
    "panda": "giant panda",
    "shark": "great white shark",
    "great white": "great white shark",
    "turtle": "sea turtle",
    "bee": "honeybee",
    "rhino": "rhinoceros",
    "polarbear": "polar bear",
}


def normalize_animal(value):
    """Only accept names in the roster; never use fuzzy matching to award a win."""
    name = re.sub(r"[^a-z\s-]", "", str(value).lower()).strip().replace("-", " ")
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"^(?:a |an |the )", "", name)
    name = name.removesuffix("s") if name not in ANIMALS and name.endswith("s") else name
    name = ALIASES.get(name, name)
    return name if name in ANIMALS else None


def new_game(target=None):
    """Start a random round; target parameter is useful for deterministic tests."""
    if target is None:
        target = random.choice(list(ANIMALS))
    if target not in ANIMALS:
        raise ValueError("Unknown target animal")
    return {
        "target": target,
        "candidates": list(ANIMALS),
        "turns": [],
        "messages": [
            {"role": "assistant", "content": (
                f"I am thinking of **one of {len(ANIMALS)} animals**. "
                "Ask yes/no questions to narrow it down, then name the animal. "
                f"You have **{MAX_TURNS} turns**. Good luck!"
            )}
        ],
        "finished": False,
        "won": False,
        "outcome": None,
    }


def finish_game(game, outcome):
    """Finish once. Returns the record to append to the session's history."""
    if game["finished"]:
        return None
    game["finished"] = True
    game["won"] = outcome == "Won"
    game["outcome"] = outcome
    quality = [turn["quality"] for turn in game["turns"]]
    return {
        "animal": game["target"],
        "outcome": outcome,
        "guesses": len(game["turns"]),
        "avg_quality": round(sum(quality) / len(quality), 1) if quality else 0.0,
        "turns": [dict(turn) for turn in game["turns"]],
    }


def play_turn(game, text, intent):
    """Apply a verified intent and return (accepted, reply, finished_record)."""
    if game["finished"]:
        return False, "This round is over. Start a new game to continue.", None
    if not isinstance(text, str) or not text.strip():
        return False, "Please type a question or an animal name.", None
    if len(text) > 240:
        return False, "Please keep your message under 240 characters.", None

    kind = intent.get("kind") if isinstance(intent, dict) else None
    value = intent.get("value", "") if isinstance(intent, dict) else ""
    if kind == "feature" and value in FEATURES:
        before = len(game["candidates"])
        yes = value in ANIMALS[game["target"]]
        game["candidates"] = [
            animal for animal in game["candidates"]
            if (value in ANIMALS[animal]) == yes
        ]
        removed = before - len(game["candidates"])
        reply = f"**{'Yes' if yes else 'No'}.** {removed} of {before} remaining animals ruled out."
        label = FEATURES[value]
    elif kind == "guess":
        animal = normalize_animal(value)
        if not animal:
            return False, (
                "I didn't recognize that animal in this game's roster. "
                "Check the animal list below the chat, or ask a yes/no question."
            ), None
        before = len(game["candidates"])
        yes = animal == game["target"]
        if yes:
            game["candidates"] = [game["target"]]
            reply = f"🎉 **You got it!** It was the **{game['target']}**."
        else:
            game["candidates"] = [candidate for candidate in game["candidates"] if candidate != animal]
            reply = f"**No**, not a {animal}. Keep investigating!"
        removed = before - len(game["candidates"])
        label = f"Guess: {animal}"
    else:
        return False, (
            "I can answer yes/no questions about animal groups, appearance, "
            "habitat, diet and behavior. Try *'Does it have wings?'* "
            "or *'Is it a polar bear?'*."
        ), None

    # Quality is an observable elimination rate, not an opaque AI 'confidence' score.
    quality = round(100 * removed / before, 1) if before else 0.0
    game["turns"].append({
        "text": text.strip(), "question": label, "answer": "Yes" if yes else "No",
        "kind": kind, "before": before, "after": len(game["candidates"]),
        "removed": removed, "quality": quality,
    })
    reply += f"  ·  **Question quality: {quality:g}%**"

    record = None
    if kind == "guess" and yes:
        record = finish_game(game, "Won")
    elif len(game["turns"]) >= MAX_TURNS:
        reply += f"\n\n⏳ No turns left. The answer was **{game['target']}**."
        record = finish_game(game, "Lost")
    return True, reply, record


def mean(values):
    return sum(values) / len(values) if values else 0.0


def game_summary(history):
    """Calculates statistics only from completed rounds."""
    guesses = [g["guesses"] for g in history]
    qualities = [t["quality"] for g in history for t in g["turns"]]
    wins = sum(g["outcome"] == "Won" for g in history)
    return {
        "games": len(history), "wins": wins,
        "win_rate": 100 * wins / len(history) if history else 0.0,
        "avg_guesses": mean(guesses), "avg_quality": mean(qualities),
    }

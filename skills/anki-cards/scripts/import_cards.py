#!/usr/bin/env python3
"""Импорт карточек в Anki через AnkiConnect.

Использование:
    python import_cards.py /tmp/anki_cards.json

Требует запущенного Anki с аддоном AnkiConnect (код 2055492159).
Формат JSON описан в SKILL.md.
"""

import json
import sys
import urllib.request

ANKI_URL = "http://localhost:8765"


def invoke(action, **params):
    """Один вызов AnkiConnect. Возвращает result или бросает исключение."""
    payload = json.dumps({
        "action": action,
        "version": 6,
        "params": params,
    }).encode("utf-8")

    req = urllib.request.Request(ANKI_URL, data=payload)
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)

    if data.get("error") is not None:
        raise RuntimeError(data["error"])
    return data["result"]


def ensure_deck(name):
    """Создаёт колоду, если её ещё нет (idempotent)."""
    invoke("createDeck", deck=name)


def build_note(card):
    """Превращает карточку из JSON в note-объект AnkiConnect.

    Путь к источнику в поля карточки не пишется — тема/источник кодируются
    тегами (поле tags).
    """
    deck = card["deck"]
    tags = card.get("tags", [])

    if card["type"] == "cloze":
        fields = {"Text": card["text"], "Extra": card.get("extra", "")}
        model = "Cloze"
    elif card["type"] == "basic":
        fields = {"Front": card["front"], "Back": card["back"]}
        model = "Basic"
    else:
        raise ValueError(f"Неизвестный тип карточки: {card['type']}")

    return {
        "deckName": deck,
        "modelName": model,
        "fields": fields,
        "tags": tags,
        "options": {"allowDuplicate": False,
                    "duplicateScope": "deck"},
    }


def main():
    if len(sys.argv) != 2:
        print("Использование: python import_cards.py <путь_к_json>")
        sys.exit(1)

    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        cards = json.load(f)

    # Создаём все нужные колоды заранее
    for deck in {c["deck"] for c in cards}:
        ensure_deck(deck)

    added, skipped = 0, 0
    for card in cards:
        note = build_note(card)
        try:
            invoke("addNote", note=note)
            added += 1
        except RuntimeError as e:
            if "duplicate" in str(e).lower():
                skipped += 1
                front = card.get("front") or card.get("text", "")[:40]
                print(f"  пропущено (дубль): {front}")
            else:
                print(f"  ОШИБКА: {e}")

    print(f"\nГотово. Добавлено: {added}, пропущено дублей: {skipped}")


if __name__ == "__main__":
    main()

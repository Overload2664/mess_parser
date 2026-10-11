# mess_parser

Reads and edits the message archives (`.dat` files) from Mario Party 4, converting between the binary file to and from a JSON file or a directory of text files.

This tool may work with other entries but no testing is done.

## Download
Either [download the tool](https://github.com/Overload2664/mess_parser/releases/latest/download/mess_reader.exe) and run commands with:
```sh
mess_reader.exe ...
```

or run it manually with (Python is required):
```sh
git clone https://github.com/Overload2664/mess_parser
cd mess_parser
python3 cli.py ...
```

## Usage

One positional argument (the `.dat`) plus exactly one conversion flag. With `--to-*` the `.dat` is the input; with `--from-*` it is the output.

| Command | Effect |
|---|---|
| `python3 cli.py game.dat --to-json game.json` | `.dat` -> JSON |
| `python3 cli.py game.dat --to-dir game_txt/` | `.dat` -> directory tree |
| `python3 cli.py new.dat --from-json game.json` | JSON -> `.dat` |
| `python3 cli.py new.dat --from-dir game_txt/` | directory tree -> `.dat` |

```sh
python3 cli.py board.dat --to-dir board_txt/
# edit the .mess files
python3 cli.py board_new.dat --from-dir board_txt/
```

### JSON

```json
{
    "mess": [
        {
            "bank": [
                { "id": 0, "message": "Mario" },
                { "id": 1, "message": "You found a <color index=1>Hidden Block<color index=7>!<wait-for-key>" }
            ]
        }
    ]
}
```

`id` is `(bank << 16) | index`. It is informational: on reading it gets ignored, so keep the order and edit the text, no need to add one manually yourself.

### Directory

```
game_txt/bank_0/0.mess
game_txt/bank_0/1.mess
game_txt/bank_1/0.mess
```

Each file holds the ID on the first line and the message text on the rest:

```
0
Mario
```

Banks are `bank_<N>`, and files are named by index. Once again the ID is informational and no need to change them if you're editing.

## Message syntax

Each byte of a message is written as one of four things:

1. **A literal character** — `A`, `5`, `!`, `…`
2. **A bracket token** — `[coin]`, `[arrow]`, `[0]`…`[9]`
3. **A magic tag** — `<newline>`, `<wait-for-key>`, `<color index=2>`
4. **A raw byte escape** — `<0x93>`

The leading clear byte (`0x0B`) and trailing terminator (`0x00`) are added automatically, so a message exported from a `.dat` re-imports as the same text.

### Literal characters

`0-9 A-Z a-z` and `! ? . , : / ( ) " ' + - & × ÷ · ° … — ‼ ⁉ ¿ ¡` plus the accented letters `Ä Ö Ü β À Á È É Ì Í Ò Ó Ù Ú Ñ à â ä ç è é ê ë î ï ô ö ù û ü ì í ò ó ú ñ Œ œ`.

Other characters (`#`, `$`, `%`, `@`, ...) have no corresponding codes and shouldn't be used.

### Bracket tokens

Glyphs with no sensible ASCII character:

| Token | Glyph |
|---|---|
| `[coin]` | coin |
| `[star]` | star |
| `[arrow]` | arrow |
| `[tilted_quotes]` | slanted quotes |
| `[degree_below]` | lowered degree |
| `[0]`…`[9]` | large digits (ordinary digits are `0`-`9`) |

### Magic tags

Written as `<name>`, case-insensitive, spelled exactly with no extra spaces.

| Tag | Meaning |
|---|---|
| `<newline>` | line break |
| `<clear>` | clear window |
| `<tab>` | advance to next tab stop |
| `<choice>` | mark this position as a selectable choice |
| `<toggle-outline>` | toggle outline/drop-shadow style |
| `<wait-for-key>` | wait for a button press |
| `<long-space>` | wide space, used for indentation |

Four tags take an `index=N` parameter:

| Tag | Valid `N` | Meaning |
|---|---|---|
| `<sprite index=N>` | 0–254 | draw inline sprite/icon `N` |
| `<audio index=N>` | 0–254 | play sound effect `N` |
| `<color index=N>` | 0–9 | set text colour to palette slot `N` |
| `<insert index=N>` | 0–254 | insert (call) message slot `N` |

Example:

```
Hello <color index=2>there<color index=7>!
```
Here `<color index=2>` changes the color to index 2 for the remaining of the text (`there`) until another color command is used.

### Raw byte escapes

`<0xNN>` is a single byte in hex, exactly two digits. If you want to specify your own codes manually and in hex for some reason, then simply write the exact bytes in hex form.

Example:
```
<0x48><0x65><0x6C><0x6C><0x70> 
```
(corresponds to `Hello`)

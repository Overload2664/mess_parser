import re

'''
hex to text:
MAGIC COMMANDS: (0-47 and 255)
0: null termination
1-9: (nothing)
10: new line
11: clear window
12: tab
13: (nothin)
14: In-line sprite, index is the number right after - 1
15: Choice marker
16: space
17-27: (nothin)
28: Play audio, index is the number right after - 1
29: Toggle outline
30: Change color from a chosen palette, the color index is the number right after - 1 (0 to 9)
31: Insert external text from insert, the insert index is the number right after - 1
32: space
33-47: (nothin)
255: block until a key press

CHARATERS: (48 to 254)
48-57: 0 to 9
58: coin
59: star
60: +
61: -
62: × (almost similar to english character x)
63: arrow
64: (empty)
65-90: A to Z
91: "
92: '
93: (
94: )
95: /
96: (empty)
97-122: a to z
123: : (colon)
124: ÷
125: · (check to see if it's actually period)
126: &
127: (empty)
128: tilted_double_qoutes
129: °
130: ,
131: ° but down instead of up
132: — (en dash I think)
133: .
134: ₋ (dash but down)
134-144: (empty)
145: Ä
146: Ö
147: Ü
148: β (beta)
149: À
150: Á
151: È
152: É
153: Ì
154: Í
155: Ò
156: Ó
157: Ù
158: Ú
159: Ñ
160-169: 0 to 9 (bigger)
170-191: (empty)
192: "
193: "
194: !
195: ?
196: ⁉
197: ‼
198: ¿
199: ¡
200-208: (empty)
209: à
210: â
211: ä
212: ç
213: è
214: é
215: ê
216: ë
217: î
218: ï
219: ô
220: ö
221: ù
222: û
223: ü
224: à
225: ì
226: í
227: ò
228: ó
229: ú
230: ñ
231: Œ
232: œ
233-253: (empty)
254: …
'''

chars = []

chars += [(n, chr(n)) for n in range(48, 58)]  # 0–9
chars += [
    (58, "[coin]"), (59, "[star]"), (60, "+"), (61, "-"),
    (62, "×"), (63, "[arrow]"), (64, ""),
]
chars += [(n, chr(n)) for n in range(65, 91)]  # A–Z
chars += [
    (91, '"'), (92, "'"), (93, "("), (94, ")"), (95, "/"), (96, ""),
]
chars += [(n, chr(n)) for n in range(97, 123)]  # a–z
chars += [
    (123, ":"), (124, "÷"), (125, "·"), (126, "&"), (127, ""),
    (128, "[tilted_quotes]"), (129, "°"), (130, ","),
    (131, "[degree_below]"), (132, "—"), (133, "."),
    (134, "₋"),
]
chars += [(n, "") for n in range(135, 145)]
chars += [
    (145, "Ä"), (146, "Ö"), (147, "Ü"), (148, "β"),
    (149, "À"), (150, "Á"), (151, "È"), (152, "É"),
    (153, "Ì"), (154, "Í"), (155, "Ò"), (156, "Ó"),
    (157, "Ù"), (158, "Ú"), (159, "Ñ"),
]
chars += [(n, f"[{n - 160}]") for n in range(160, 170)]  # larger 0–9
chars += [(n, "") for n in range(170, 192)]
chars += [
    (192, '"'), (193, '"'), (194, "!"), (195, "?"),
    (196, "⁉"), (197, "‼"), (198, "¿"), (199, "¡"),
]
chars += [(n, "") for n in range(200, 209)]
chars += [
    (209, "à"), (210, "â"), (211, "ä"), (212, "ç"),
    (213, "è"), (214, "é"), (215, "ê"), (216, "ë"),
    (217, "î"), (218, "ï"), (219, "ô"), (220, "ö"),
    (221, "ù"), (222, "û"), (223, "ü"), (224, "à"),
    (225, "ì"), (226, "í"), (227, "ò"), (228, "ó"),
    (229, "ú"), (230, "ñ"), (231, "Œ"), (232, "œ"),
]
chars += [(n, "") for n in range(233, 254)]
chars += [(254, "…")]

code_to_char = dict(chars)
char_to_code = {char: code for code, char in chars if char}
char_to_code['"'] = 91 # 93, 192 and 193 are the same character so I chose the one most used in MP4

def _require_index(index: int | None) -> int:
    if index is None:
        raise ValueError("this command requires an index byte")
    if index < 1:
        raise ValueError("index byte must be at least 1")
    return index

def magic_syntax(command: int, index: int | None = None) -> str:
    """Return readable syntax for a magic command and its optional following byte."""
    if not 0 <= command <= 255:
        raise ValueError("command must be between 0 and 255")

    if command == 0:
        return "<null>"
    if 1 <= command <= 9 or 13 <= command <= 13 or 17 <= command <= 27 or 33 <= command <= 47:
        return "<unused>"
    if command == 10:
        return "<newline>"
    if command == 11:
        return "<clear>"
    if command == 12:
        return "<tab>"
    if command == 14:
        return f"<sprite index={_require_index(index) - 1}>"
    if command == 15:
        return "<choice>"
    if command in (16, 32):
        return " "
    if command == 28:
        return f"<audio index={_require_index(index) - 1}>"
    if command == 29:
        return "<toggle-outline>"
    if command == 30:
        value = _require_index(index)
        if not 1 <= value <= 10:
            raise ValueError("color parameter must be between 1 and 10 (color indices 0–9)")
        return f"<color index={value - 1}>"
    if command == 31:
        return f"<insert index={_require_index(index) - 1}>"
    if command == 255:
        return "<wait-for-key>"
    else:
        return ""

simple_commands = {
    "<null>": 0,
    "<newline>": 10,
    "<clear>": 11,
    "<tab>": 12,
    "<choice>": 15,
    " ": 16,  # Also represents command 32; see note below.
    "<toggle-outline>": 29,
    "<wait-for-key>": 255,
}

complex_commands = {
    "sprite": 14,
    "audio": 28,
    "color": 30,
    "insert": 31,
}

def is_simple_command(command: int) -> bool:
    # 32 is also acceptable for space
    return command in simple_commands.values() or command == 32

def is_complex_command(command: int) -> bool:
    return command in complex_commands.values()

def parse_magic_syntax(syntax: str) -> tuple[int, int | None]:
    """Parse a syntax token and return (command, following_index_byte)."""
    if(syntax == " "):
        return simple_commands[syntax]

    token = syntax.strip().lower()

    if token in simple_commands:
        return (simple_commands[token],)

    match = re.fullmatch(r"<(sprite|audio|color|insert) index=(\d+)>", token)
    if match:
        kind, index = match.groups()
        index = int(index)

        max_index = 9 if kind == "color" else 254

        if not 0 <= index <= max_index:
            raise ValueError(f"{kind} index must be between 0 and {max_index}")

        return (complex_commands[kind], index + 1)

    raise ValueError(f"Unrecognized magic syntax: {syntax!r}")

def format_magic_byte(value: int) -> str:
    """Format a byte as a two-digit hexadecimal token, such as <0x33>."""
    if not 0 <= value <= 0xFF:
        raise ValueError("value must be between 0 and 255")
    return f"<0x{value:02X}>"

def parse_magic_byte(token: str) -> int:
    """Parse a token such as '<0x33>' and return its byte value."""
    match = re.fullmatch(r"<0x([0-9a-fA-F]{2})>", token.strip())
    if not match:
        raise ValueError(f"Invalid byte token: {token!r}")
    return int(match.group(1), 16)

__all__ = ["code_to_char", "char_to_code", "magic_syntax", "is_simple_command", "parse_magic_syntax", "format_magic_byte", "parse_magic_byte"]

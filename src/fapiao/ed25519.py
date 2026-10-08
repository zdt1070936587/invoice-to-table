"""Ed25519 签名与验签，算法按 RFC 8032。"""

from __future__ import annotations

import hashlib

_P = 2**255 - 19
_L = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)


def _sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def _inv(value: int) -> int:
    return pow(value, _P - 2, _P)


def _recover_x(y_coord: int, sign: int) -> int | None:
    if y_coord >= _P:
        return None
    y2 = (y_coord * y_coord) % _P
    x2 = ((y2 - 1) * _inv((_D * y2 + 1) % _P)) % _P
    if x2 == 0:
        if sign:
            return None
        return 0
    x_coord = pow(x2, (_P + 3) // 8, _P)
    if (x_coord * x_coord - x2) % _P != 0:
        x_coord = (x_coord * _I) % _P
    if (x_coord * x_coord - x2) % _P != 0:
        return None
    if (x_coord & 1) != sign:
        x_coord = _P - x_coord
    return x_coord


class _Point:
    def __init__(self, x_coord: int, y_coord: int, z_coord: int, t_coord: int) -> None:
        self.x = x_coord
        self.y = y_coord
        self.z = z_coord
        self.t = t_coord

    def affine(self) -> tuple[int, int]:
        z_inv = _inv(self.z)
        return (self.x * z_inv) % _P, (self.y * z_inv) % _P


def _encode_point(point: _Point) -> bytes:
    x_coord, y_coord = point.affine()
    bits = y_coord | ((x_coord & 1) << 255)
    return bits.to_bytes(32, "little")


def _decode_point(data: bytes) -> _Point | None:
    if len(data) != 32:
        return None
    raw = int.from_bytes(data, "little")
    sign = (raw >> 255) & 1
    y_coord = raw & ((1 << 255) - 1)
    x_coord = _recover_x(y_coord, sign)
    if x_coord is None:
        return None
    return _Point(x_coord, y_coord, 1, (x_coord * y_coord) % _P)


def _add(left: _Point, right: _Point) -> _Point:
    a_val = (left.y - left.x) * (right.y - right.x) % _P
    b_val = (left.y + left.x) * (right.y + right.x) % _P
    c_val = (2 * _D * left.t * right.t) % _P
    d_val = (2 * left.z * right.z) % _P
    e_val = (b_val - a_val) % _P
    f_val = (d_val - c_val) % _P
    g_val = (d_val + c_val) % _P
    h_val = (b_val + a_val) % _P
    return _Point(
        e_val * f_val % _P,
        g_val * h_val % _P,
        f_val * g_val % _P,
        e_val * h_val % _P,
    )


def _scalarmult(point: _Point, scalar: int) -> _Point:
    result = _Point(0, 1, 1, 0)
    addend = point
    while scalar:
        if scalar & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        scalar >>= 1
    return result


def _base_point() -> _Point:
    y_coord = (4 * _inv(5)) % _P
    x_coord = _recover_x(y_coord, 0)
    if x_coord is None:
        raise RuntimeError("Ed25519 基点不可用")
    return _Point(x_coord, y_coord, 1, (x_coord * y_coord) % _P)


_B = _base_point()


def _expand_secret(secret: bytes) -> tuple[int, bytes]:
    digest = _sha512(secret)
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def public_key(secret: bytes) -> bytes:
    scalar, _prefix = _expand_secret(secret)
    return _encode_point(_scalarmult(_B, scalar))


def sign(message: bytes, secret: bytes) -> bytes:
    scalar, prefix = _expand_secret(secret)
    pub = _encode_point(_scalarmult(_B, scalar))
    nonce = int.from_bytes(_sha512(prefix + message), "little") % _L
    commitment = _encode_point(_scalarmult(_B, nonce))
    challenge = int.from_bytes(_sha512(commitment + pub + message), "little") % _L
    signature_s = (nonce + challenge * scalar) % _L
    return commitment + signature_s.to_bytes(32, "little")


def verify(message: bytes, signature: bytes, pub: bytes) -> bool:
    if len(signature) != 64 or len(pub) != 32:
        return False
    commitment = _decode_point(signature[:32])
    point_a = _decode_point(pub)
    if commitment is None or point_a is None:
        return False
    signature_s = int.from_bytes(signature[32:], "little")
    if signature_s >= _L:
        return False
    challenge = int.from_bytes(_sha512(signature[:32] + pub + message), "little") % _L
    left = _scalarmult(_B, signature_s)
    right = _add(commitment, _scalarmult(point_a, challenge))
    return left.affine() == right.affine()

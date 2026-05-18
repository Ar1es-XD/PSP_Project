import zlib


def shard_for(value: str, shard_count: int) -> int:
    return zlib.crc32(value.encode("utf-8")) % shard_count


def is_local_shard(value: str, shard_id: int, shard_count: int) -> bool:
    return shard_for(value, shard_count) == shard_id

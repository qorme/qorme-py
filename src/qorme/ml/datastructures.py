from datetime import datetime
from uuid import UUID, uuid4

import msgspec
import xxhash

from qorme.utils.datetime import microseconds_since, utcnow


class MLConfigurationData(msgspec.Struct):
    classes: list[str]
    features: list[str]


class MLConfiguration(msgspec.Struct):
    id: int
    data: MLConfigurationData

    def get_sample_hash(self, instance) -> int:
        d = xxhash.xxh64()
        for feature in self.data.features:
            val = instance.get_feature(feature)
            d.update(val.encode())
            d.update(b"\x00")
        return d.intdigest()

    def decode_target(self, target: int) -> list[str]:
        return [name for i, name in enumerate(self.data.classes) if (target & (1 << i))]


class SampleUpdate(msgspec.Struct):
    hash_value: int
    updated_at: int
    target: int
    stable: bool


class MLPrediction(msgspec.Struct, omit_defaults=True):
    uid: UUID
    timestamp: datetime
    configuration_id: int
    sample_hash: int
    predicted: int
    duration: int
    data: dict[str, str] = {}


class MLModel(msgspec.Struct, omit_defaults=True):
    name: str
    updated_at: int
    configuration: MLConfiguration | None = None
    sample_updates: list[SampleUpdate] = []
    samples: dict[int, SampleUpdate] = {}

    def predict(self, instance) -> MLPrediction | None:
        if not self.configuration:
            return

        start_ts = utcnow()
        sample_hash = self.configuration.get_sample_hash(instance)
        if not (sample := self.samples.get(sample_hash)):
            return

        assert sample.stable
        return MLPrediction(
            uuid4(),
            start_ts,
            self.configuration.id,
            sample_hash,
            sample.target,
            microseconds_since(start_ts),
        )

    def decode_target(self, target: int) -> list[str]:
        return self.configuration.decode_target(target) if self.configuration else []


class MLModelsUpdate(msgspec.Struct):
    timestamp: int
    models: dict[str, list[MLModel]]

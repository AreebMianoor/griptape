from attr import define, field, Factory
from griptape.artifacts import BlobArtifact, BaseArtifact, InfoArtifact, ListArtifact
from griptape.drivers import BaseBlobToolMemoryDriver, MemoryBlobToolMemoryDriver
from griptape.memory.tool import BaseToolMemory


@define
class BlobToolMemory(BaseToolMemory):
    driver: BaseBlobToolMemoryDriver = field(
        default=Factory(lambda: MemoryBlobToolMemoryDriver()),
        kw_only=True
    )

    def process_output(self, tool_activity: callable, artifact: BaseArtifact) -> BaseArtifact:
        from griptape.utils import J2

        if isinstance(artifact, BlobArtifact):
            artifact_ids = [self.driver.save(artifact)]
        elif isinstance(artifact, ListArtifact):
            artifact_ids = [self.driver.save(a) for a in artifact.value if isinstance(a, BlobArtifact)]
        else:
            artifact_ids = []

        if len(artifact_ids) > 0:
            output = J2("memory/tool/blob.j2").render(
                memory_name=self.name,
                tool_name=tool_activity.__self__.name,
                activity_name=tool_activity.name,
                artifact_ids=str.join(", ", artifact_ids)
            )

            return InfoArtifact(output)
        else:
            return artifact

    def load_namespace_artifacts(self, namespace: str) -> list[BaseArtifact]:
        return [self.driver.load(namespace)]

from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_summarizer import Seq2SeqSummarizer


class StubRuntime:
    def __init__(self, output: str) -> None:
        self.output = output

    @property
    def status(self):
        return None

    def generate(self, _prompt: str, *, max_new_tokens: int) -> str:
        assert max_new_tokens == 128
        return self.output


def make_summarizer(output: str) -> Seq2SeqSummarizer:
    settings = ModelSettings()
    return Seq2SeqSummarizer(settings, runtime=StubRuntime(output))


def test_summary_keeps_original_sentence_omitted_by_model() -> None:
    message = (
        "Please move my appointment to Friday. I also cannot download the education "
        "leaflet from the portal."
    )
    summarizer = make_summarizer("Please move my appointment to Friday.")

    result = summarizer.summarize(message)

    assert "Please move my appointment to Friday." in result
    assert "I also cannot download the education leaflet from the portal." in result


def test_summary_does_not_repeat_sentence_when_model_covers_it() -> None:
    message = "Please move my appointment to Friday."
    summarizer = make_summarizer("Please move my appointment to Friday.")

    assert summarizer.summarize(message) == "Please move my appointment to Friday."

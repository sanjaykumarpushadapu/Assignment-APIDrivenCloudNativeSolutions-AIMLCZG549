from diabetes_support.infrastructure.model_settings import ModelSettings
from diabetes_support.infrastructure.seq2seq_summarizer import Seq2SeqSummarizer


class StubRuntime:
    def __init__(self, output: str) -> None:
        self.output = output
        self.decoding_options: dict[str, int] = {}

    @property
    def status(self):
        return None

    def generate(self, _prompt: str, *, max_new_tokens: int, **_decoding: int) -> str:
        assert max_new_tokens == 128
        self.decoding_options = _decoding
        return self.output


def make_summarizer(output: str) -> Seq2SeqSummarizer:
    settings = ModelSettings()
    return Seq2SeqSummarizer(settings, runtime=StubRuntime(output))


def test_summary_does_not_append_source_sentences_to_a_paraphrase() -> None:
    message = (
        "My diabetes education appointment is on Monday morning. "
        "I cannot attend because of work. Could it be moved to Friday after 2 pm? "
        "Please ask the appointments team to confirm whether a suitable slot is "
        "available. I have not received confirmation of a new booking yet."
    )
    generated = (
        "Cannot attend Monday's diabetes education appointment because of work; "
        "requests Friday after 2 pm, awaiting confirmation."
    )

    result = make_summarizer(generated).summarize(message)

    assert result == generated
    assert result.count("Friday after 2 pm") == 1
    assert len(result.split()) < len(message.split())


def test_blank_generation_falls_back_to_original_message() -> None:
    message = "Please move my appointment to Friday."

    assert make_summarizer("  ").summarize(message) == message


def test_summary_uses_beam_search_and_blocks_repeated_phrases() -> None:
    runtime = StubRuntime("Please move my appointment to Friday.")
    summarizer = Seq2SeqSummarizer(ModelSettings(), runtime=runtime)

    summarizer.summarize("Please move my appointment to Friday.")

    assert runtime.decoding_options == {
        "num_beams": 4,
        "no_repeat_ngram_size": 3,
    }


def test_summary_does_not_repeat_sentence_when_model_covers_it() -> None:
    message = "Please move my appointment to Friday."
    summarizer = make_summarizer("Please move my appointment to Friday.")

    assert summarizer.summarize(message) == "Please move my appointment to Friday."

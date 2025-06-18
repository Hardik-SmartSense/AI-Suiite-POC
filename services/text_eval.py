import jiwer

transformation = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemovePunctuation(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.Strip()
])


def evaluate_text(original_text, generated_text):
    # Defensive checks
    if not isinstance(original_text, str) or not isinstance(generated_text,
                                                            str):
        raise ValueError("Both inputs must be strings")

    ref = transformation(original_text)
    hyp = transformation(generated_text)

    if not ref.strip():
        raise ValueError("Reference transcript is empty after normalization.")
    if not hyp.strip():
        raise ValueError("Generated transcript is empty after normalization.")

    # Compute all metrics safely
    measures = jiwer.compute_measures(ref, hyp)
    return round(measures["wer"]*100, 2)

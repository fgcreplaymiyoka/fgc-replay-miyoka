import itertools
import numpy as np
from numpy.typing import NDArray
from miyoka.libs.scene_vectorizer import SceneVectorizer as SceneVectorizerBase
from miyoka.sf6.constants import ARROWS, CLASSIC_INPUTS


class SceneVectorizer(SceneVectorizerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vocabulary = self._build_vocabs()

        # Bigram for arrows
        perms = itertools.permutations(ARROWS, 2)
        for p in perms:
            token = ">".join(p)
            self.vocabulary.append(token)

        self.vocab_size = len(self.vocabulary)
        self.token_to_index = {v: i for i, v in enumerate(self.vocabulary)}
        self.index_to_token = {i: v for i, v in enumerate(self.vocabulary)}

    def get_feature_names_out(self) -> list[str]:
        return self.vocabulary

    # TODO: Maybe action input and arrow input should be separately extracted as features.
    # e.g. '1' '2' '3' ... '1>2', '1>3', ... 'lp', 'mp'
    def vectorize(self, inputs: list[str]) -> NDArray[np.float64]:
        optimized_inputs = []
        prev_t = ""
        for t in inputs:
            # Deduplicate the consecutive inputs
            if t == prev_t:
                continue

            optimized_inputs.append(t)

            # Extract features as the arrow direction changes
            if prev_t != "" and t[0] != prev_t[0]:
                bigram_token = ">".join([prev_t[0], t[0]])
                optimized_inputs.append(bigram_token)

            prev_t = t

        indexes = np.array([self.token_to_index[t] for t in optimized_inputs])
        values, counts = np.unique(indexes, return_counts=True)
        vector = np.zeros(self.vocab_size)

        for v, c in zip(values, counts):
            vector[v] = c

        print(f"scene_vector: {vector[:10]}")
        print(f"np.nonzero(vector): {np.nonzero(vector)}")

        if np.all(vector == 0):
            raise Exception("ERROR: All vector is zero!")

        return vector

    def _build_vocabs(self) -> list[str]:
        vocabs = []

        for arrow in ARROWS:
            for input_comb in self._input_combinations():
                vocab = arrow
                if input_comb:
                    input = " ".join(input_comb)
                    vocab += f" {input}"
                vocabs.append(vocab)

        return vocabs

    def _input_combinations(self):
        yield ""  # no input

        # for inputs in [CLASSIC_INPUTS, MODERN_INPUTS]:
        for inputs in [CLASSIC_INPUTS]:
            for r in range(1, len(inputs) + 1):
                comb = itertools.combinations(inputs, r)

                for i in comb:
                    yield i

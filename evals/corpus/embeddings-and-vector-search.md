<!-- source: https://oodarag.example/handbook/embeddings-and-vector-search -->
# Embeddings and Vector Search

An embedding maps a passage to a fixed-length vector so that passages with
similar meaning land near each other. Retrieval then becomes a nearest
neighbour search: embed the question, compare it to every chunk vector, and
return the closest.

## Cosine similarity

Similarity is measured by the cosine of the angle between two vectors, which
ignores their magnitudes and compares only direction. If every vector is
L2-normalized when it is stored, cosine similarity reduces to a plain dot
product, which is one multiply-accumulate per dimension and needs no division
at query time. Normalizing on write is therefore both faster and less
error-prone than normalizing on read.

## The hashing trick

A dependency-free embedder can be built without any trained model by hashing
tokens into buckets. Each token is mapped to one of d buckets by a stable hash
and added with a deterministic plus or minus one sign, so that collisions
cancel out on average instead of accumulating into a spurious bias. Term
frequency enters sublinearly, as one plus the logarithm of the count, for the
same reason BM25 saturates it. Adding character n-grams of each token at a
lower weight gives subword robustness, so "chunking" and "chunked" land near
each other without a learned vocabulary.

This is a real embedding in the geometric sense and a weak one in the semantic
sense: it captures lexical overlap and morphology, not synonymy. It exists so
that the pipeline answers questions on a laptop with no model download, no API
key and no network, and so the dense arm is exercised in CI. Swapping in a
hosted embedder is a change behind one interface.

## Exhaustive search versus approximate

Exhaustive scoring compares the query to every vector. At a few hundred
thousand chunks this is milliseconds and it is exactly correct, which makes it
the right default; approximate nearest neighbour structures trade recall for
latency and only pay off when the corpus is much larger. Whatever the index,
the vectors themselves should be stored compactly, as raw 32-bit floats rather
than JSON.

## Caching

Embeddings are keyed by the content hash of the text that produced them, so
re-indexing an unchanged corpus costs no compute. A timestamp-based cache key
would be wrong: mirrors, rebases and re-uploads all change timestamps without
changing a byte of content.

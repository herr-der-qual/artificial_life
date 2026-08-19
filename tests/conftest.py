import gc

# pymunk Body/Shape objects hold a reference cycle by design (body.shape and
# shape.body point at each other). CPython's cyclic collector can sweep such
# cycles in an order pymunk's cffi cleanup (shapefree) doesn't expect, which
# can segfault - this shows up in this suite once enough Worlds (each with
# dozens of Body/Shape pairs) have been created and discarded across tests.
# Disabling the cyclic collector avoids it triggering mid-run. This is a
# known pymunk/cffi + CPython GC interaction, not specific to this project;
# see the "pymunk GC segfault" notes if it needs deeper investigation.
gc.disable()

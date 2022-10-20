# Edith SDK #

This project is an extension of [evolve-sdk-python](https://github.com/zepben/evolve-sdk-python) for the Edith project.

It provides functionality to create synthetic feeders from an Edith network hosted in the Energy workbench server,
and apply certain scenarios to them to modify the network.

# Usage #

Functionality is implemented on the NetworkConsumerClient from the Evolve SDK, so to use simply do the following:

    from zepben.evolve import connect_with_password
    from zepben.edith import NetworkConsumerClient, usage_point_proportional_allocator
    
    channel = connect_with_password(client_id="some_client_id", username="test", password="secret", host="host", port=443)
    client = NetworkConsumerClient(channel)
    mutator = usage_point_proportional_allocator(
        proportion=30,
        edith_customers=["9995435452"],
        allow_duplicate_customers=True,  # exclude to prevent adding a customer to multiple usage points
        seed=1234  # exclude for non-deterministic allocation
    )
    num_allocations = client.create_synthetic_feeder(
        "some_feeder_mrid",
        mutator=allocator
    )
    synthetic_feeder = client.service
    # ... do stuff with synthetic feeder ...

# Mutator Functions #

## Usage Point Allocator ##

The `usage_point_proportional_allocator` function creates a mutator that distributes NMI names across a percentage
of usage points. It will use up all provided names before reusing any. In other words, it will not reuse a name unless
the number of allocations (`num_allocations`) is greater than the length of `edith_customers`. By default, it will stop
allocating NMI names once it uses up all provided names, unless `allow_duplicate_customers` is set to `True`.
This allocator also removes an existing NMI on each usage point it adds a NMI to, if there exists one.

Example: A synthetic feeder is created on a feeder with 5 usage points: UP1, UP2, UP3, UP4, and UP5. The allocator is
a `usage_point_proportional_allocator(proportion=60, edith_customers=["A", "B", "C"])`. One possible result of the
allocation is for UP5 to receive name "A", UP2 to receive name "B", and UP3 to receive name "C". UP1 and UP4 would not
be modified in this case.

The `seed` parameter is used to seed the pseudorandom number generator, making the random allocations reproducible. An
example is provided in the above "Usage" section.

## Line Weakener ##

    mutator = line_weakener(
        weakening_percentage=30,
        use_weakest_when_necessary=False  # exclude to use weakest line type when necessary
    )

The line weakener decreases the amp rating and modifies impedance on lines by selecting from a built-in catalogue of 
linecodes. For each line, the applied linecode must match its phase count and whether its voltage category (HV or LV).
Suppose a line has an amp rating of 300A. with a `weakening_percentage` of 30, the linecode used will have an amp rating
of at most (100 - 30)% of 300A, i.e. 210A. Linecode "ABC4w:70ABC" would be used if the line is 3-phase LV, with an amp
rating of 175A. Note that if there are multiple linecodes that fit the criteria, the one with the highest amp rating is
used. If there are no linecodes that fit the criteria and `use_weakest_when_necessary` is `True`, then the
lowest-amp-rating linecode that matches the phase and voltage criteria is used, if there is one. Otherwise, the line is
left unmodified.

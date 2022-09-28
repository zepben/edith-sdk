# Edith SDK #

This project is an extension of [evolve-sdk-python](https://github.com/zepben/evolve-sdk-python) for the Edith project.

It provides functionality to create synthetic feeders from an Edith network hosted in the Energy workbench server,
and apply certain scenarios to them to modify the network.

# Usage #

Functionality is implemented on the NetworkConsumerClient from the Evolve SDK, so to use simply do the following:

    from zepben.edith import NetworkConsumerClient, connect_with_password, distribution_transformer_proportional_allocator_creator
    
    channel = connect_with_password(client_id="some_client_id", username="test", password="secret", host="host", port=443)
    client = NetworkConsumerClient(channel)
    allocator = usage_point_proportional_allocator(proportion=30, edith_customers=["9995435452"])
    synthetic_feeder, num_allocations = client.create_synthetic_feeder(
        "some_feeder_mrid",
        allocator=allocator,
        seed=1234  # exclude for non-deterministic allocation
    )
    # ... do stuff with synthetic feeder ...
    
The `usage_point_proportional_allocator` function creates an allocator that distributes NMI names across a percentage
of usage points. It will use up all provided names before reusing any. In other words, it will not reuse a name unless
the number of modifications (`num_allocations`) is greater than the length of `edith_customers`.

Example: A synthetic feeder is created on a feeder with 5 usage points: UP1, UP2, UP3, UP4, and UP5. The allocator is
a `usage_point_proportional_allocator(proportion=60, edith_customers=["A", "B", "C"])`. One possible result of the
allocation is for UP5 to receive name "A", UP2 to receive name "B", and UP3 to receive name "C". UP1 and UP4 would not
be modified in this case.

The `seed` parameter is used to seed the pseudorandom number generator, making the random allocations reproducible.

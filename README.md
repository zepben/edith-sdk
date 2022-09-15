# Edith SDK #

This project is an extension of [evolve-sdk-python](https://github.com/zepben/evolve-sdk-python) for the Edith project.

It provides functionality to create synthetic feeders from an Edith network hosted in the Energy workbench server,
and apply certain scenarios to them to modify the network.

# Usage #

Functionality is implemented on the NetworkConsumerClient from the evolve SDK, so to use simply do the following:

    from zepben.edith import NetworkConsumerClient, connect_with_password, distribution_transformer_proportional_allocator_creator
    
    channel = connect_with_password(client_id="some_client_id", username="test", password="secret", host="host", port=443)
    client = NetworkConsumerClient(channel)
    allocator = distribution_transformer_proportional_allocator_creator(proportion=30, edith_customers=["9995435452"])
    synthetic_feeder = client.create_synthetic_feeder("some_feeder_mrid", allocator=allocator)
    # ... do stuff with synthetic feeder ...
    

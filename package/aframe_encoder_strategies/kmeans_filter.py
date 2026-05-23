"""
FIRST PASS (INIT)
    for each aframe
        using 128 samples and 8 previous samples, 
        determine the best fitting (least squares) prev_sample_influence coeffs
        from error, obtain pulse scale
        from coeffs, obtain the lpc_filter
    
    now we have the lpc_filter for all aframes

    directly set lpc_base to first aframe's lpc filter
    directly set scale_initial to first aframe's scale

    let's build the lpc_codebooks
    using all subsequent aframes,
        create kmeans(64) for lpc filter
        store each centroid in the codebook 0

        subtract centroid from lpc filter to get error
        create kmeans(64) for error
        store each centroid in the codebook 1

        subtract centroid from error to get error error
        create kmeans(64) for error error
        store each centroid in the codebook 2
    
SECOND PASS (ENCODE)
    for each aframe
        encode by using the 3 centroid id as lpc_codebook_indexes
        get prev_sample_influence coeffs from reconstituted lpc_filter
        apply coeffs to 128 samples and 8 previous samples to get error
        calculate pulses from error

"""


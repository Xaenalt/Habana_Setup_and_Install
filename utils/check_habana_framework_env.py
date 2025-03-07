###############################################################################
# Copyright (C) 2022 Habana Labs, Ltd. an Intel Company
# All Rights Reserved.
#
# Unauthorized copying of this file or any element(s) within it, via any medium
# is strictly prohibited.
# This file contains Habana Labs, Ltd. proprietary and confidential information
# and is subject to the confidentiality and license agreements under which it
# was provided.
#
###############################################################################

import argparse
import os
import concurrent.futures

def parse_arguments():
    parser = argparse.ArgumentParser(description="Check health of HPU for either TensorFlow/PyTorch")

    parser.add_argument("--cards",
                        default=1,
                        type=int,
                        required=False,
                        help="Set number of cards to test (default: 1)")
    parser.add_argument("--framework",
                        default="tensorflow",
                        type=str,
                        required=False,
                        nargs="?",
                        choices=("tensorflow", "pytorch"),
                        help="ML Framework to test (default: tensorflow)")

    args = parser.parse_args()
    print(f"Configuration: {args}")

    return args

def tensorflow_test(device_id=0):
    """ Checks health of HPU through running a basic
    TensorFlow example on HPU

    Args:
        device_id (int, optional): ID of HPU. Defaults to 0.
    """

    os.environ["HLS_MODULE_ID"] = str(device_id)

    try:
        import tensorflow as tf
        import habana_frameworks.tensorflow as htf
        htf.load_habana_module()
    except Exception as e:
        print(f"Card {device_id} Failed to initialize Habana TensorFlow: {str(e)}")
        raise

    try:
        x = tf.constant(2)
        y = x + x

        assert y.numpy() == 4, 'Sanity check failed: Wrong Add output'
        assert 'hpu' in y.device.lower(), 'Sanity check failed: Operation not executed on Habana Device'
    except (RuntimeError, AssertionError) as e:
        print(f"Card {device_id} Failure: {e}")
        raise

def pytorch_test(device_id=0):
    """ Checks health of HPU through running a basic
    PyTorch example on HPU

    Args:
        device_id (int, optional): ID of HPU. Defaults to 0.
    """

    os.environ["ID"] = str(device_id)

    try:
        import torch
        import habana_frameworks.torch.core
    except Exception as e:
        print(f"Card {device_id} Failed to initialize Habana PyTorch: {str(e)}")
        raise

    try:
        x = torch.tensor([2]).to('hpu')
        y = x + x

        assert y == 4, 'Sanity check failed: Wrong Add output'
        assert 'hpu' in y.device.type.lower(), 'Sanity check failed: Operation not executed on Habana Device'
    except (RuntimeError, AssertionError) as e:
        print(f"Card {device_id} Failure: {e}")
        raise


if __name__ == '__main__':
    args = parse_arguments()
    fw_test = None

    if args.framework == "tensorflow":
        fw_test = tensorflow_test
    elif args.framework == "pytorch":
        fw_test = pytorch_test
    else:
        print("No valid framework chosen. Exiting")
        exit(1)

    try:
        with concurrent.futures.ProcessPoolExecutor() as executor:
            for device_id, res in zip(range(args.cards), executor.map(fw_test, range(args.cards))):
                print(f"Card {device_id} PASSED")
    except Exception as e:
            print(f"Failed to initialize Habana, error: {str(e)}")
            print(f"Check FAILED")
            exit(1)

    print(f"Check PASSED for {args.cards} cards")
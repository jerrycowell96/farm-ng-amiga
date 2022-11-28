# Copyright (c) farm-ng, inc.
#
# Licensed under the Amiga Development Kit License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/farm-ng/amiga-dev-kit/blob/main/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations

import argparse
import asyncio

import cv2
import numpy as np
from farm_ng.oak import oak_pb2
from farm_ng.oak.camera_client import OakCameraClient
from farm_ng.oak.camera_client import OakCameraClientConfig
from farm_ng.oak.camera_client import OakCameraServiceState


async def main(address: str, port: int, stream_every_n: int) -> None:
    # configure the camera client
    config = OakCameraClientConfig(address=address, port=port)
    client = OakCameraClient(config)

    # get the streaming object
    response_stream = client.stream_frames(every_n=stream_every_n)

    # start the streaming service
    await client.connect_to_service()

    while True:
        # query the service state
        # NOTE: This could be done asynchronously with client.poll_service_state()
        #       as in other examples, such as camera_client_gui
        state: OakCameraServiceState = await client.get_state()

        if state.value != oak_pb2.OakServiceState.RUNNING:
            print("Camera is not streaming!")
            continue

        response: oak_pb2.StreamFramesReply = await response_stream.read()
        if response and response.status == oak_pb2.ReplyStatus.OK:
            # get the sync frame
            frame: oak_pb2.OakSyncFrame = response.frame
            print(f"Got frame: {frame.sequence_num}")
            print(f"Device info: {frame.device_info}")
            print(f"Timestamp: {frame.rgb.meta.timestamp}")
            print("#################################\n")

            # cast image data bytes to numpy and decode
            # NOTE: explore frame.[rgb, disparity, left, right]
            image = np.frombuffer(frame.rgb.image_data, dtype="uint8")
            image = cv2.imdecode(image, cv2.IMREAD_UNCHANGED)

            # visualize the image
            cv2.namedWindow("image", cv2.WINDOW_NORMAL)
            cv2.imshow("image", image)
            cv2.waitKey(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="amiga-camera-app")
    parser.add_argument("--port", type=int, required=True, help="The camera port.")
    parser.add_argument("--address", type=str, default="localhost", help="The camera address")
    parser.add_argument("--stream-every-n", type=int, default=4, help="Streaming frequency")
    args = parser.parse_args()

    asyncio.run(main(args.address, args.port, args.stream_every_n))

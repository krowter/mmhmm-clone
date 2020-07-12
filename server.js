// const tf = require("@tensorflow/tfjs-node");
const tf = require("@tensorflow/tfjs-node-gpu");
const bodyPix = require("@tensorflow-models/body-pix");
const express = require("express");
const app = express();
const port = 9000;

(async () => {
  const net = await bodyPix.load({
    architecture: "MobileNetV1",
    outputStride: 16,
    multiplier: 0.75,
    quantBytes: 2,
  });

  app.post("/mask-frame", async (req, res) => {
    try {
      var chunks = [];
      req.on("data", (chunk) => {
        chunks.push(chunk);
      });
      req.on("end", async () => {
        const image = tf.node.decodeImage(Buffer.concat(chunks));
        segmentation = await net.segmentPerson(image, {
          flipHorizontal: false,
          internalResolution: "medium",
          segmentationThreshold: 0.7,
        });
        res.writeHead(200, { "Content-Type": "application/octet-stream" });
        res.write(Buffer.from(segmentation.data));
        res.end();
        tf.dispose(image);
      });
    } catch (err) {
      console.log(err);
    }
  });

  app.listen(port, () => console.log(`Listening on port ${port}`));
})();

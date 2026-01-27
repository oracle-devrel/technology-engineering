var express = require("express");
var router = express.Router();

/* GET home page. */
router.get("/", function (req, res, next) {
  res.json({
    title: "ODA Pro Style API",
    version: "1.0.0",
    message: "Welcome!",
  });
});

module.exports = router;

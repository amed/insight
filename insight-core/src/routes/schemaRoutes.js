const express = require('express');
const asyncReqWrapper = require('../utils/asyncReqWrapper');
const controller = require('../controllers/schemaController');

const router = express.Router();

router.get('/', controller.list);
router.get('/:name/summary', asyncReqWrapper(controller.summary));

module.exports = router;

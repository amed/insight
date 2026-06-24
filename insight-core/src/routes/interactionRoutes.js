const express = require('express');
const upload = require('../middleware/upload');
const asyncReqWrapper = require('../utils/asyncReqWrapper');
const controller = require('../controllers/interactionController');

const router = express.Router();

router.post('/', upload.single('file'), asyncReqWrapper(controller.create));
router.get('/:id', asyncReqWrapper(controller.getOne));

module.exports = router;

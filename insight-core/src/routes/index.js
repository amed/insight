const express = require('express');
const listEndpoints = require('express-list-endpoints');
const interactionRoutes = require('./interactionRoutes');
const schemaRoutes = require('./schemaRoutes');

const router = express.Router();

// List every available endpoint with http method
router.get('/', (req, res) => {
  res.json(listEndpoints(req.app).map(({ path, methods }) => ({ path, methods })));
});

router.use('/interactions', interactionRoutes);
router.use('/schemas', schemaRoutes);

module.exports = router;

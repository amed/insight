// An error with an HTTP status. The error middleware turns it into a response.
class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'HttpError';
  }
}

module.exports = HttpError;

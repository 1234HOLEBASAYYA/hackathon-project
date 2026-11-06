function successResponse(res, data, message = 'Success', statusCode = 200) {
  return res.status(statusCode).json({
    status: 'success',
    message,
    data
  });
}

function errorResponse(res, message = 'Operation failed', statusCode = 400, details = null) {
  return res.status(statusCode).json({
    status: 'error',
    message,
    details
  });
}

module.exports = {
  successResponse,
  errorResponse
};


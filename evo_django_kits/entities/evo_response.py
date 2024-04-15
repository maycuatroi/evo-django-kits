from rest_framework.response import Response


class EvoResponse(Response):
    def __init__(
        self,
        message=None,
        data=None,
        status=None,
        headers=None,
    ):
        status = status or 200

        response = {"message": message}
        if data is not None:
            response["data"] = data

        super().__init__(response, status=status, headers=headers)

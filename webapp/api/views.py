"""HTTP views for skill-gap analysis and role discovery."""

from analyzer.engine import analyze
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .matcher_singleton import get_matcher
from .serializers import (
    SkillGapRequestSerializer,
    SkillGapResponseSerializer,
    available_roles,
)


def _serialize_result(result):
    """Serialize analyzer dataclasses without coupling the analyzer to DRF."""
    report = result.gap_report
    return {
        "role_title": result.role_title,
        "overall_gap_score": report.overall_gap_score,
        "overall_match_percent": report.overall_match_percent,
        "skill_gaps": [
            {
                "skill": item.skill,
                "required_level": item.required_level,
                "user_level": item.user_level,
                "weighted_gap": item.weighted_gap,
                "status": item.status,
            }
            for item in report.skill_gaps
        ],
        "recommendations": [
            {
                "skill": item.skill,
                "priority_rank": item.priority_rank,
                "resources": item.resources,
            }
            for item in result.recommendations
        ],
        "unmatched_inputs": result.unmatched_inputs,
    }


class SkillGapView(APIView):
    def post(self, request):
        request_serializer = SkillGapRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(request_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = request_serializer.validated_data
        try:
            result = analyze(
                data["job_title"],
                data["skills"],
                matcher=get_matcher(),
                top_n=data["top_n"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = SkillGapResponseSerializer(_serialize_result(result))
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RolesView(APIView):
    def get(self, request):
        return Response(available_roles(), status=status.HTTP_200_OK)

from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from groups.models import Group
from traits.models import Trait
from .models import Pet
from .serializers import PetSerializer


class PetView(APIView, PageNumberPagination):
    def get(self, request):
        trait_name = request.query_params.get("trait")

        if trait_name:
            pets_in_traits = Pet.objects.filter(traits__name__iexact=trait_name)
            result_page = self.paginate_queryset(pets_in_traits, request)
        else:
            pets = Pet.objects.all()
            result_page = self.paginate_queryset(pets, request)

        serializer = PetSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trait_list = serializer.validated_data.pop("traits")
        group_data = serializer.validated_data.pop("group")

        group_obj, _ = Group.objects.get_or_create(
            scientific_name__iexact=group_data["scientific_name"], defaults=group_data
        )

        pet_object = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait in trait_list:
            trait_obj, _ = Trait.objects.get_or_create(
                name__iexact=trait["name"], defaults=trait
            )
            pet_object.traits.add(trait_obj)

        serializer = PetSerializer(pet_object)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PetDetailView(APIView, PageNumberPagination):
    def get(self, request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet)
        return Response(serializer.data)

    def delete(self, request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, pet_id):
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        trait_list = serializer.validated_data.pop("traits", None)
        group_data = serializer.validated_data.pop("group", None)

        if trait_list:
            new_traits = [
                Trait.objects.get_or_create(name__iexact=trait["name"], defaults=trait)[
                    0
                ]
                for trait in trait_list
            ]
            pet.traits.set(new_traits)

        if group_data:
            group_obj, _ = Group.objects.get_or_create(
                scientific_name=group_data["scientific_name"], defaults=group_data
            )
            pet.group = group_obj

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        pet.save()
        serializer = PetSerializer(pet)
        return Response(serializer.data, status=status.HTTP_200_OK)

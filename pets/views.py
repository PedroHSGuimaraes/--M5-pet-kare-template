from groups.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, Request, Response, status
from traits.models import Trait
from .models import Pet
from .serializers import PetSerializer
from rest_framework.pagination import PageNumberPagination


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        trait_name = request.query_params.get("trait")
        if trait_name:
            pets_in_traits = Pet.objects.filter(traits__name__iexact=trait_name)
            result_page = self.paginate_queryset(pets_in_traits, request)

        else:
            pets = Pet.objects.all()
            result_page = self.paginate_queryset(pets, request)

        serializer = PetSerializer(result_page, many=True)

        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trait_list = serializer.validated_data.pop("traits")

        group_data = serializer.validated_data.pop("group")
        group_obj = Group.objects.filter(
            scientific_name__iexact=group_data["scientific_name"]
        ).first()
        if not group_obj:
            group_obj = Group.objects.create(**group_data)

        pet_object = Pet.objects.create(**serializer.validated_data, group=group_obj)

        for trait in trait_list:
            trait_obj = Trait.objects.filter(name__iexact=trait["name"]).first()

            if not trait_obj:
                trait_obj = Trait.objects.create(**trait)

            pet_object.traits.add(trait_obj)

        serializer = PetSerializer(pet_object)

        return Response(serializer.data, status.HTTP_201_CREATED)


class PetDetailView(APIView, PageNumberPagination):
    def get(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet)

        return Response(serializer.data)

    def delete(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)

        pet.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id: int) -> Response:
        pet = get_object_or_404(Pet, id=pet_id)
        serializer = PetSerializer(pet, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)

        trait_list: list = serializer.validated_data.pop("traits", None)
        group_data: dict = serializer.validated_data.pop("group", None)

        if trait_list:
            new_traits = []
            for trait in trait_list:
                try:
                    trait_obj_update = Trait.objects.get(name__iexact=trait["name"])

                except Trait.DoesNotExist:
                    trait_obj_update = Trait.objects.create(**trait)
                new_traits.append(trait_obj_update)
            pet.traits.set(new_traits)

        if group_data:
            try:
                group_obj_update = Group.objects.get(
                    scientific_name=group_data["scientific_name"]
                )
            except Group.DoesNotExist:
                group_obj_update = Group.objects.create(**group_data)
            pet.group = group_obj_update

        for k, v in serializer.validated_data.items():
            setattr(pet, k, v)

        pet.save()
        serializer = PetSerializer(pet)

        return Response(serializer.data, status=status.HTTP_200_K)

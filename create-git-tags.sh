#!/bin/bash -eux

# Using the CLI

token="$1"
marked_for_publishing="$2"
branch="$3"
rock_repository="$4"
rock_commit="$5"
track=${6:-$(echo $branch | cut -d '/' -f 2)}
risk="$7"
# use skip_build_tag when only publishing the release tag
# i.e., if channel/<track>/<rock>/<version>/<base>/<revision> already exists
skip_build_tag="$8"

# Move to rock repo and create tag
pushd $ROCK_PROJECT_CHECKOUT_LOCATION
git config user.email "rocks-dev@lists.canonical.com"
git config user.name "ROCKS Team"
git remote add upstream-rock https://rocks-team:${token}@github.com/${rock_repository}

tag_prefix=$(echo $branch | awk -F"/" '{print $1"/"$2}')
build_tags=()
release_tags=()
while IFS= read -r rock
do 
    rock_name="$(echo $rock | cut -d ',' -f 2)"
    rock_version="$(echo $rock | cut -d ',' -f 3)"
    rock_base="$(echo $rock | cut -d ',' -f 4)"
    rock_revision="$(echo $rock | cut -d ',' -f 6)"
    oci_tags="$(echo $rock | cut -d ',' -f 7)"

    if [ "$skip_build_tag" != "1" ] && [ "$skip_build_tag" != "true" ]
    then
        tag_name="${tag_prefix}/${rock_name}/${rock_version}/${rock_base}/${rock_revision}"

        git tag -a \
            -m "New revision ${rock_revision} of ${rock_name} ${rock_version} created (OCI tags: ${oci_tags})" \
            $tag_name $rock_commit

        git push upstream-rock $tag_name
        build_tags+=( $tag_name )
    fi 

    if [ ! -z $risk ]
    then
        # There's a risk in the channel branch, so let's release the ROCK
        release_tag="release/${rock_name}/${rock_revision}/${track}/${risk}"
        git tag -a \
            -m "Release tag for revision ${rock_revision} of ${rock_name} ${rock_version} to ${track}/${risk}" \
            $release_tag $rock_commit

        git push upstream-rock $release_tag
        release_tags+=( $release_tag )
    fi
done < "${marked_for_publishing}"
popd

echo "::set-output name=build-tags::${build_tags[@]}"
echo "::set-output name=release-tags::${release_tags[@]}"
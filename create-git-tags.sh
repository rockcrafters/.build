#!/bin/bash -eux

# In theory it is possible to do this via the GitHub API
# https://docs.github.com/en/rest/git/tags
# But for some reason it is failing for "verification" purposes
# (see the create-git-tags.py if trying to solve the issue)

# Using the CLI instead

token="$1"
marked_for_publishing="$2"
branch="$3"
risk="$4"
rock_repository="$5"
rock_commit="$6"

# Move to rock repo and create tag
pushd $ROCK_PROJECT_CHECKOUT_LOCATION
git config user.email "rocks-dev@lists.canonical.com"
git config user.name "ROCKS Team"
git remote add upstream-rock https://rocks-team:${token}@github.com/${rock_repository}

tag_prefix=$(echo $branch | awk -F"/" '{print $1"/"$2}')
all_tags=()
while IFS= read -r rock
do 
    rock_name="$(echo $rock | cut -d ',' -f 2)"
    rock_version="$(echo $rock | cut -d ',' -f 3)"
    rock_base="$(echo $rock | cut -d ',' -f 4)"
    rock_revision="$(echo $rock | cut -d ',' -f 6)"
    oci_tags="$(echo $rock | cut -d ',' -f 7)"

    tag_name="${tag_prefix}/${rock_version}/${rock_name}/${rock_base}/${rock_revision}/${risk}"

    git tag -a \
        -m "New revision ${rock_revision} of ${rock_name} ${rock_version} created (OCI tags: ${oci_tags})" \
        $tag_name $rock_commit

    git push upstream-rock $tag_name
    all_tags+=( $tag_name )
done < "${marked_for_publishing}"
popd

echo "::set-output name=git-tags::${all_tags[@]}"
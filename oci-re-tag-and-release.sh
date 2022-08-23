#!/bin/bash -eux

# Re-tag an existing ROCK and create the GH release

token="$1"
new_oci_tags=""
for risk in $RELEASE_FOR_RISKS
do
    new_oci_tags="${new_oci_tags} ${ROCK_VERSION}-${BASE}_${risk}_$REVISION"
    new_oci_tags="${new_oci_tags} ${ROCK_VERSION}-${BASE}_${risk}"
    new_oci_tags="${new_oci_tags} ${ROCK_VERSION}_${risk}"
    new_oci_tags="${new_oci_tags} ${risk}"
    if [ "${risk}" == "stable" ]
    then 
        new_oci_tags="${new_oci_tags} $TRACK"
    fi
done

IS_LTS=0
if `ubuntu-distro-info -a -f | grep $BASE | grep LTS >/dev/null`
then
    IS_LTS=1
fi

# TODO: we are unnecessarily pushing the whole ROCK once more
# just because we want to reuse the cpc-build-tools.oci-registry-upload script.
# Instead, we just needed to push indexes...so we should refactor the code
args="$OCI_ARCHIVE $ROCK_NAME _ _ $IS_LTS ${new_oci_tags}"
retry=0
$ROCKS_CICD_CHECKOUT_LOCATION/src/Tag-and-Publish.sh $args || retry=1
if [ $retry -eq 1 ]
then
    $ROCKS_CICD_CHECKOUT_LOCATION/src/Tag-and-Publish.sh $args 
    # Sometimes pushes are reset by peer 
fi

echo "Re-tag and publishing successful"

cat>gh_release.txt<<EOF
{
  "tag_name":"$RELEASE_TAG",
  "name":"$RELEASE_TAG",
  "body":"$ROCK_NAME is now in $TRACK/$RISK. New OCI tags: $(echo $new_oci_tags | tr ' ' ',')",
  "draft":false,
  "prerelease":false,
  "generate_release_notes":false
}
EOF

curl \
  -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $token" \
  https://api.github.com/repos/${ROCK_REPO}/releases \
  -d @gh_release.txt

rm gh_release.txt || true
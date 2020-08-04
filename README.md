# Easy Probe Builder for Sysdig Agent

Update Packages if outdated

```
for distro in $(echo "trusty xenial bionic focal groovy"); do mkdir files/${distro}; curl -vO http://security.ubuntu.com/ubuntu/dists/$distro-security/main/binary-amd64/Packages.gz ; mv Packages.gz files/$distro/Packages.gz  ; done
```
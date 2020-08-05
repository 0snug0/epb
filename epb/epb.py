import click
from os import getcwd, mkdir, path, system
from sys import stderr
from git import Repo
import docker
from json import dumps, loads
import requests
import gzip
import re


cwd = getcwd()
basedir = "%s/sysdig-probe-builder" % (cwd)

@click.command()
@click.option('-R', '--registry', default="", help="Docker v2 registry the airgapped nodes can reach")
@click.option('-r', '--repo', default="sysdig-probe-builder", show_default=True, help="DONT USE THIS UNLESS YOU ARE SURE -- Repository you will store the images in")
@click.option('-b', '--basedir', default="%s/sysdig-probe-builder" % (cwd), show_default=True, help="Empty base directory where we'll build the probes")
@click.option('-w', '--dir-workspace', default="%s/workspace" % (basedir), show_default=True, help="DON'T CHANGE")
@click.option('-k', '--dir-kernels', default="%s/kernels" % (basedir), show_default=True, help="DON'T CHANGE")
@click.option('-s', '--dir-sysdig', default="%s/sysdig" % (basedir), show_default=True, help="DON'T CHANGE")
@click.option('-d', '--docker-sock', default="/var/run/docker.sock", show_default=True, help="DON'T CONANGE THIS UNLESS YOU ARE SURE - builder needs access to docker.sock")
@click.option('-a', '--agent-version', default="10.3.0", show_default=True, help="sysdig agent version") 
@click.option('-u', '--uname', default="4.4.0-186-generic", show_default=True, help="uname -r from the nodes")
@click.option('-m', '--mirror', default="http://security.ubuntu.com/ubuntu/", show_default=True, help="Debian file repo")
@click.option('-U', '--ubuntu-version', default="20.04", show_default=True, help="Ubuntu version")
@click.option('-p', '--push-docker', default=False, show_default=True, help="Push all image builds to docker repo")

def build(registry, repo, basedir, dir_workspace, dir_kernels, dir_sysdig, docker_sock, agent_version, uname, mirror, ubuntu_version, push_docker):

    ubuntu_names =   {"14.04": "trusty",
                    "16.04": "xenial",
                    "18.04": "bionic",
                    "20.04": "focal",
                    "20.10": "groovy"}
    ubuntu_name = ubuntu_names[ubuntu_version]

    def dirs_create():
        mkdirs = [basedir]
        dirs = [dir_workspace, dir_kernels, dir_sysdig]
        for dir in dirs:
            mkdirs.append(path.join(basedir,dir))
        for makedir in mkdirs:
            try:
                mkdir(makedir)
            except FileExistsError:
                print("WARN: %s exist" % (makedir), file=stderr)
            except OSError as error:
                print(error)

    
    def sysdig_git():
        try:
            repo = Repo.clone_from("https://github.com/draios/sysdig", dir_sysdig, branch="agent-release-%s" % (agent_version))
        except Exception as error:
            print("ERROR: %s" % (error.status))

    client = docker.DockerClient(base_url='unix:/%s' % (docker_sock))

    def docker_image_build(registry, repo, tag, dir):
        imagetag = registry + repo + ":" + tag
        build = client.images.build(path=dir, tag=imagetag)
        print("LOG: %s" % (build[0]))
        for log in build[1]:
            print("LOG: %s" % (log))
        return "LOG: %s" % (build[0])
    
    def docker_image_push(registry, repo, tag, stream=False, decode=False):
        repo = path.join(registry, '') + repo
        push = client.images.push(repository=repo, tag=tag)
        print(push)

    def docker_run_probe_builder(registry, repo, tag, volumes, agent_version):
        imagetag = registry + repo + ":" + tag
        command = "-B -- -p sysdigcloud-probe -v %s -k CustomUbuntu" % (agent_version)
        run = client.containers.run(imagetag, command, volumes=volumes)

    def packages_file_downloader(ubuntu_name):
        '''Downloads the Packages files for the ubuntu distro'''
        package_link="http://security.ubuntu.com/ubuntu/dists/" + ubuntu_name + "-security/main/binary-amd64/Packages.gz" 
        print(package_link)
        r = requests.get(package_link)
        print(r.status_code)
        with open(path.join(dir_workspace, ubuntu_name, "Packages.gz"), 'wb') as f:
            f.write(r.content)

    def search_packages(packages_file):
        package_links = []
        headers_dep = re.search('\d+.\d+.\d+-\d+', uname)[0]
        for package in ["linux-image-%s" % (uname), "linux-modules-%s" % (uname), "linux-headers-%s" % (uname), "linux-headers-%s" %(headers_dep)]:
            with gzip.open(packages_file, 'rt') as infile:
                print("searching gzip")
                found = False                
                for line in infile:
                    if "Package: %s" % (package) in line:
                        found = True
                        print("Found:", line.split()[1] )
                    elif found and "Filename: " in line:
                        package_links.append(line.split()[1])
                        break
        return package_links

    def download_packages(mirror, package_links, dir_kernels):
        for package_link in package_links:
            fn = package_link.split("/")[-1]
            print(fn)
            url = path.join(mirror, "ubuntu", package_link)
            r = requests.get(url)
            print(r.status_code)
            with open(path.join(dir_kernels, fn), 'wb') as file:
                file.write(r.content)


    # dirs_create()
    # sysdig_git()
    probe_builder = path.join(basedir, dir_sysdig, 'probe-builder')
    docker_image_build(registry, repo, "latest", probe_builder) # make these var
    # if push_docker:
    #     docker_image_push(registry, repo, "latest")
    # # download_packages(mirror, dir_kernels, package_links)
    # # packages_file_downloader(ubuntu_name)
    # packages_file = path.join(cwd, "files" , ubuntu_name, "Packages.gz")
    # package_links = search_packages(packages_file)
    # download_packages("http://security.ubuntu.com/", package_links, dir_kernels)
    volumes = {docker_sock: {"bind": "/var/run/docker.sock"}, dir_workspace: {"bind": "/workspace"}, dir_sysdig: {"bind": "/sysdig"}, dir_kernels: {"bind": "/kernels"}}
    docker_run_probe_builder(registry, repo, "latest", volumes, agent_version)
if __name__ == '__main__':
    build()
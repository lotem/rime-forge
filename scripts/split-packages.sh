#!/bin/bash

github_user=${USER}
source_branch=master

rewrite_git_history() {
  local package="$1"
  git filter-branch --prune-empty --subdirectory-filter ${package} -- ${source_branch}
  # clean up
  git reset --hard
  git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d
  git reflog expire --expire=now --all
  git gc --aggressive --prune=now
}

push_package() {
  local package="$1"
  # push to GitHub
  git remote rename origin local
  git remote add origin https://github.com/${github_user}/rime-${package}.git
  git push -u origin master
}

excluded_dirs=':packages:scripts:jyutping:moe:'
target_dir="$PWD/packages"

main() {
  mkdir -p "${target_dir}"
  local package
  for package in *; do
    if [[ -d "${package}" ]] && ! [[ "${excluded_dirs}" =~ ":${package}:" ]]; then
        local package_repo_path="${target_dir}/rime-${package}"
        git clone "$PWD" "${package_repo_path}"
        pushd "${package_repo_path}"
        rewrite_git_history ${package}
        push_package ${package}
        popd
    fi
  done
}

main

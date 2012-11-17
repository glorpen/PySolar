# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/dev-python/apse/apse-0.2-r1.ebuild,v 1.2 2010/07/23 19:53:35 arfrever Exp $

EAPI="3"
#PYTHON_DEPEND="2"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="3.*"

inherit distutils python

DESCRIPTION="Approximate String Matching in Python."
HOMEPAGE="http://www.personal.psu.edu/staff/i/u/iua1/python/apse/"

EGIT_REPO_URI="git://github.com/glorpen/bumblepyy.git"
SRC_URI="file:///mnt/sandbox/workspace/pysolar/src/dist/solar.tar.bz2"

SLOT="0"
KEYWORDS="~amd64 ~ia64 ~ppc ~ppc64 ~x86"
IUSE="gnome-shell"

DEPEND="
    dev-python/configobj
    dev-python/python-daemon
    gnome-shell? (
	gnome-base/gnome-shell
	app-admin/eselect-gnome-shell-extensions
    )
"
RDEPEND="${DEPEND}"

#src_unpack(){
#    echo '';
#}

S="${WORKDIR}/solar"

src_prepare(){
    cd "${S}/src"
    distutils_src_prepare || die
}

src_compile(){
    cd "${S}/src"
    distutils_src_compile || die
}

src_install(){
    cd "${S}/src"
    distutils_src_install || die
    
    if use gnome-shell; then
	insinto /usr/share/gnome-shell/extensions
	doins -r "${S}"/gnome-shell/*@*
    fi
    
    #newconfd "${FILESDIR}/bumblepyy.confd" bumblepyy
    #newinitd "${FILESDIR}/bumblepyy.initd" bumblepyy
}

pkg_postinst() {
	ebegin "Updating list of installed extensions"
	eselect gnome-shell-extensions update
	eend $?
}

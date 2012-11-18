# Copyright 1999-2010 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
# $Header: /var/cvsroot/gentoo-x86/dev-python/apse/apse-0.2-r1.ebuild,v 1.2 2010/07/23 19:53:35 arfrever Exp $

EAPI="3"
SUPPORT_PYTHON_ABIS="1"
RESTRICT_PYTHON_ABIS="3.*"

inherit distutils python

DESCRIPTION="DBus service for providing lightness and battery levels for Logitech Solar devices."
HOMEPAGE="https://bitbucket.org/glorpen/pysolar"

SRC_URI="https://bitbucket.org/glorpen/${PN}/get/v${PV}.tar.bz2 -> ${PN}-v${PV}.tar.bz2"

SLOT="0"
KEYWORDS="amd64 ~ia64 ~ppc ~ppc64 x86"
IUSE="gnome-shell +daemon"

DEPEND="
    dev-python/configobj
    dev-python/python-daemon
    gnome-shell? (
		gnome-base/gnome-shell
		app-admin/eselect-gnome-shell-extensions
    )
    daemon? ( dev-python/python-daemon )
"
RDEPEND="${DEPEND}"

src_prepare(){
	S=$( ls -1d "${WORKDIR}/glorpen-pysolar-"* ) || die
	
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
    
    use daemon && newinitd "${FILESDIR}/pysolar.init.d" pysolar
}

pkg_postinst() {
	ebegin "Updating list of installed extensions"
	eselect gnome-shell-extensions update
	eend $?
}

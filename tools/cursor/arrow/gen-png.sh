##
## Copyright © 2020 Endless OS Foundation LLC.
##
## This file is part of clubhouse
## (see https://github.com/endlessm/clubhouse).
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License along
## with this program; if not, write to the Free Software Foundation, Inc.,
## 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##
for j in *.svg
do
    for i in $(cat ../sizes)
    do
        n=$(echo $j | sed 's/.svg//g')
        org.inkscape.Inkscape -e ${n}_${i}.png -h $i $j
    done
done
